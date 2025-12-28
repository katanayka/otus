package main

import (
	"io"
	"testing"
)

func testLogger() *Logger {
	return NewLogger(io.Discard, LevelInfo)
}

func TestParseAppsInstalledValid(t *testing.T) {
	logger := testLogger()
	line := "idfa\tdev-1\t55.5\t42.0\t1,2,3"
	item, err := parseAppsInstalled(line, logger)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if item.DevType != "idfa" || item.DevID != "dev-1" {
		t.Fatalf("unexpected device data: %#v", item)
	}
	if len(item.Apps) != 3 {
		t.Fatalf("unexpected apps: %#v", item.Apps)
	}
}

func TestParseAppsInstalledInvalidApps(t *testing.T) {
	logger := testLogger()
	line := "gaid\tdev-2\t1.0\t2.0\t1,foo,3"
	item, err := parseAppsInstalled(line, logger)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(item.Apps) != 2 {
		t.Fatalf("unexpected apps: %#v", item.Apps)
	}
}

func TestParseAppsInstalledInvalidCoords(t *testing.T) {
	logger := testLogger()
	line := "gaid\tdev-3\tbad\t2.0\t1"
	if _, err := parseAppsInstalled(line, logger); err == nil {
		t.Fatalf("expected error")
	}
}

func TestParseAppsInstalledInvalidLine(t *testing.T) {
	logger := testLogger()
	if _, err := parseAppsInstalled("broken line", logger); err == nil {
		t.Fatalf("expected error")
	}
}
