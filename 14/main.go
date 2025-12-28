package main

import (
	"bufio"
	"compress/gzip"
	"errors"
	"flag"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"runtime"
	"sort"
	"strings"
	"sync"
	"sync/atomic"
	"time"

	"memcload/appsinstalled"

	proto "github.com/golang/protobuf/proto"
)

const (
	normalErrRate  = 0.01
	taskQueueSize  = 10000
	memcTimeoutSec = 2
)

type Job struct {
	memcAddr string
	apps     *AppsInstalled
}

type Stats struct {
	processed uint64
	errors    uint64
}

func (s *Stats) IncProcessed() {
	atomic.AddUint64(&s.processed, 1)
}

func (s *Stats) IncErrors() {
	atomic.AddUint64(&s.errors, 1)
}

func (s *Stats) Processed() uint64 {
	return atomic.LoadUint64(&s.processed)
}

func (s *Stats) Errors() uint64 {
	return atomic.LoadUint64(&s.errors)
}

func main() {
	var (
		logPath  = flag.String("log", "", "Log file path")
		dryRun   = flag.Bool("dry", false, "Dry run (do not write to memcache)")
		pattern  = flag.String("pattern", "/data/appsinstalled/*.tsv.gz", "Glob pattern for input files")
		idfaAddr = flag.String("idfa", "127.0.0.1:33013", "Memcache address for idfa")
		gaidAddr = flag.String("gaid", "127.0.0.1:33014", "Memcache address for gaid")
		adidAddr = flag.String("adid", "127.0.0.1:33015", "Memcache address for adid")
		dvidAddr = flag.String("dvid", "127.0.0.1:33016", "Memcache address for dvid")
		workers  = flag.Int("workers", runtime.NumCPU(), "Number of worker goroutines")
	)
	flag.Parse()

	level := LevelInfo
	if *dryRun {
		level = LevelDebug
	}
	logger := NewLogger(selectWriter(*logPath), level)

	if *workers < 1 {
		logger.Infof("Workers must be >= 1, falling back to 1")
		*workers = 1
	}

	deviceMemc := map[string]string{
		"idfa": *idfaAddr,
		"gaid": *gaidAddr,
		"adid": *adidAddr,
		"dvid": *dvidAddr,
	}

	logger.Infof("Memc loader started with options: dry=%v, pattern=%s, workers=%d", *dryRun, *pattern, *workers)

	files, err := filepath.Glob(*pattern)
	if err != nil {
		logger.Errorf("Invalid pattern: %s", err)
		os.Exit(1)
	}
	sort.Strings(files)

	for _, file := range files {
		if err := processFile(file, deviceMemc, *dryRun, *workers, logger); err != nil {
			logger.Errorf("Failed processing %s: %s", file, err)
		}
	}
}

func selectWriter(path string) io.Writer {
	if path == "" {
		return os.Stdout
	}
	file, err := os.OpenFile(path, os.O_CREATE|os.O_APPEND|os.O_WRONLY, 0o644)
	if err != nil {
		fmt.Fprintf(os.Stderr, "cannot open log file: %s\n", err)
		return os.Stdout
	}
	return file
}

func processFile(
	path string,
	deviceMemc map[string]string,
	dryRun bool,
	workers int,
	logger *Logger,
) error {
	logger.Infof("Processing %s", path)
	stats := &Stats{}
	jobs := make(chan Job, taskQueueSize)
	var wg sync.WaitGroup

	for i := 0; i < workers; i++ {
		wg.Add(1)
		go worker(jobs, stats, dryRun, logger, &wg)
	}

	if err := readFile(path, deviceMemc, jobs, stats, logger); err != nil {
		logger.Errorf("Read error for %s: %s", path, err)
	}

	close(jobs)
	wg.Wait()

	if stats.Processed() == 0 {
		return dotRename(path)
	}
	errRate := float64(stats.Errors()) / float64(stats.Processed())
	if errRate < normalErrRate {
		logger.Infof("Acceptable error rate (%f). Successfull load", errRate)
	} else {
		logger.Errorf("High error rate (%f > %f). Failed load", errRate, normalErrRate)
	}
	return dotRename(path)
}

func readFile(
	path string,
	deviceMemc map[string]string,
	jobs chan<- Job,
	stats *Stats,
	logger *Logger,
) error {
	file, err := os.Open(path)
	if err != nil {
		return err
	}
	defer file.Close()

	reader, err := gzip.NewReader(file)
	if err != nil {
		return err
	}
	defer reader.Close()

	scanner := bufio.NewScanner(reader)
	buffer := make([]byte, 0, 64*1024)
	scanner.Buffer(buffer, 10*1024*1024)

	for scanner.Scan() {
		line := scanner.Text()
		if strings.TrimSpace(line) == "" {
			continue
		}
		appsInstalled, err := parseAppsInstalled(line, logger)
		if err != nil {
			stats.IncErrors()
			continue
		}
		memcAddr, ok := deviceMemc[appsInstalled.DevType]
		if !ok || memcAddr == "" {
			stats.IncErrors()
			logger.Errorf("Unknown device type: %s", appsInstalled.DevType)
			continue
		}
		jobs <- Job{memcAddr: memcAddr, apps: appsInstalled}
	}
	if err := scanner.Err(); err != nil {
		stats.IncErrors()
		return err
	}
	return nil
}

func worker(jobs <-chan Job, stats *Stats, dryRun bool, logger *Logger, wg *sync.WaitGroup) {
	defer wg.Done()
	clients := map[string]*MemcacheClient{}
	timeout := time.Duration(memcTimeoutSec) * time.Second
	for job := range jobs {
		key := fmt.Sprintf("%s:%s", job.apps.DevType, job.apps.DevID)
		data, err := buildUserApps(job.apps)
		if err != nil {
			stats.IncErrors()
			logger.Errorf("Cannot serialize %s: %s", key, err)
			continue
		}
		if dryRun {
			// logger.Debugf("%s - %s -> %s", job.memcAddr, key, formatApps(job.apps))
			stats.IncProcessed()
			continue
		}
		client := clients[job.memcAddr]
		if client == nil {
			client = NewMemcacheClient(job.memcAddr, timeout)
			clients[job.memcAddr] = client
		}
		if err := client.Set(key, data); err != nil {
			stats.IncErrors()
			logger.Errorf("Cannot write to memc %s: %s", job.memcAddr, err)
			continue
		}
		stats.IncProcessed()
	}
	for _, client := range clients {
		client.Close()
	}
}

func buildUserApps(apps *AppsInstalled) ([]byte, error) {
	ua := &appsinstalled.UserApps{
		Apps: apps.Apps,
		Lat:  &apps.Lat,
		Lon:  &apps.Lon,
	}
	data, err := proto.Marshal(ua)
	if err != nil {
		return nil, err
	}
	return data, nil
}

func formatApps(apps *AppsInstalled) string {
	parts := make([]string, 0, len(apps.Apps))
	for _, app := range apps.Apps {
		parts = append(parts, fmt.Sprintf("apps: %d", app))
	}
	parts = append(parts, fmt.Sprintf("lat: %f lon: %f", apps.Lat, apps.Lon))
	return strings.Join(parts, " ")
}

func dotRename(path string) error {
	dir, file := filepath.Split(path)
	if file == "" {
		return errors.New("invalid filename")
	}
	newPath := filepath.Join(dir, "."+file)
	return os.Rename(path, newPath)
}
