package main

import (
	"errors"
	"fmt"
	"strconv"
	"strings"
)

type AppsInstalled struct {
	DevType string
	DevID   string
	Lat     float64
	Lon     float64
	Apps    []uint32
}

func parseAppsInstalled(line string, logger *Logger) (*AppsInstalled, error) {
	line = strings.TrimSpace(line)
	if line == "" {
		return nil, errors.New("empty line")
	}
	parts := strings.Split(line, "\t")
	if len(parts) < 5 {
		return nil, fmt.Errorf("invalid line: %s", line)
	}
	devType, devID, latRaw, lonRaw, rawApps := parts[0], parts[1], parts[2], parts[3], parts[4]
	if devType == "" || devID == "" {
		return nil, fmt.Errorf("missing device identifiers: %s", line)
	}

	apps, invalid := parseApps(rawApps)
	if invalid > 0 && logger != nil {
		logger.Infof("Not all user apps are digits: `%s`", line)
	}

	lat, err := strconv.ParseFloat(latRaw, 64)
	if err != nil {
		if logger != nil {
			logger.Infof("Invalid geo coords: `%s`", line)
		}
		return nil, err
	}
	lon, err := strconv.ParseFloat(lonRaw, 64)
	if err != nil {
		if logger != nil {
			logger.Infof("Invalid geo coords: `%s`", line)
		}
		return nil, err
	}

	return &AppsInstalled{
		DevType: devType,
		DevID:   devID,
		Lat:     lat,
		Lon:     lon,
		Apps:    apps,
	}, nil
}

func parseApps(rawApps string) ([]uint32, int) {
	if rawApps == "" {
		return nil, 0
	}
	items := strings.Split(rawApps, ",")
	apps := make([]uint32, 0, len(items))
	invalid := 0
	for _, item := range items {
		item = strings.TrimSpace(item)
		if item == "" {
			continue
		}
		value, err := strconv.Atoi(item)
		if err != nil {
			invalid++
			continue
		}
		if value < 0 {
			invalid++
			continue
		}
		apps = append(apps, uint32(value))
	}
	return apps, invalid
}
