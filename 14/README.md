# Homework 14: Memcache Loader (Go)

Go port of the memcache loader from Homework 12. Parses TSV dumps and loads
protobuf values into a memcache cluster.

## Structure
- `main.go` - loader implementation
- `parser.go` - TSV parsing helpers
- `memcache.go` - minimal memcache client
- `appsinstalled/appsinstalled.pb.go` - protobuf model
- `appsinstalled.proto` - proto schema
- `parser_test.go` - parsing tests

## Requirements
- Go 1.22+
- memcached instances for idfa/gaid/adid/dvid (or use `--dry`)

## Setup
Run from the `14/` directory.

```bash
go mod download
```

## Run
```bash
go run . --pattern="data/*.tsv.gz" --dry
```

Set a custom workers count:
```bash
go run . --pattern="data/*.tsv.gz" --workers=8 --dry
```

## CLI options
- `--pattern` - input glob (default: `/data/appsinstalled/*.tsv.gz`)
- `--dry` - dry run (log only)
- `--workers` - number of worker goroutines
- `--log` - log file path (default: stdout)
- `--idfa`, `--gaid`, `--adid`, `--dvid` - memcache addresses

## Tests
```bash
go test ./...
```

## Formatting
```bash
gofmt -w .
```

## Pre-commit
```bash
pre-commit install -c .pre-commit-config.yaml
pre-commit run --all-files
```

## CI
GitHub Actions runs gofmt checks and tests on every push/PR that touches `14/**`.
