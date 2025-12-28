package main

import (
	"fmt"
	"io"
	"log"
	"time"
)

type LogLevel int

const (
	LevelDebug LogLevel = iota
	LevelInfo
	LevelError
)

type Logger struct {
	level  LogLevel
	logger *log.Logger
}

func NewLogger(out io.Writer, level LogLevel) *Logger {
	return &Logger{
		level:  level,
		logger: log.New(out, "", 0),
	}
}

func (l *Logger) Debugf(format string, args ...any) {
	l.logf(LevelDebug, "D", format, args...)
}

func (l *Logger) Infof(format string, args ...any) {
	l.logf(LevelInfo, "I", format, args...)
}

func (l *Logger) Errorf(format string, args ...any) {
	l.logf(LevelError, "E", format, args...)
}

func (l *Logger) logf(level LogLevel, prefix string, format string, args ...any) {
	if level < l.level {
		return
	}
	timestamp := time.Now().Format("2006.01.02 15:04:05")
	l.logger.Printf("[%s] %s %s", timestamp, prefix, fmt.Sprintf(format, args...))
}
