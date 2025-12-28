package main

import (
	"bufio"
	"fmt"
	"net"
	"strings"
	"time"
)

type MemcacheClient struct {
	addr    string
	timeout time.Duration
	conn    net.Conn
	rw      *bufio.ReadWriter
}

func NewMemcacheClient(addr string, timeout time.Duration) *MemcacheClient {
	return &MemcacheClient{addr: addr, timeout: timeout}
}

func (c *MemcacheClient) Connect() error {
	if c.conn != nil {
		return nil
	}
	conn, err := net.DialTimeout("tcp", c.addr, c.timeout)
	if err != nil {
		return err
	}
	c.conn = conn
	c.rw = bufio.NewReadWriter(bufio.NewReader(conn), bufio.NewWriter(conn))
	return nil
}

func (c *MemcacheClient) Close() {
	if c.conn != nil {
		_ = c.conn.Close()
		c.conn = nil
		c.rw = nil
	}
}

func (c *MemcacheClient) Set(key string, value []byte) error {
	if err := c.Connect(); err != nil {
		return err
	}
	if err := c.conn.SetDeadline(time.Now().Add(c.timeout)); err != nil {
		return err
	}
	if _, err := fmt.Fprintf(c.rw, "set %s 0 0 %d\r\n", key, len(value)); err != nil {
		c.Close()
		return err
	}
	if _, err := c.rw.Write(value); err != nil {
		c.Close()
		return err
	}
	if _, err := c.rw.WriteString("\r\n"); err != nil {
		c.Close()
		return err
	}
	if err := c.rw.Flush(); err != nil {
		c.Close()
		return err
	}
	line, err := c.rw.ReadString('\n')
	if err != nil {
		c.Close()
		return err
	}
	if strings.TrimSpace(line) != "STORED" {
		return fmt.Errorf("memcache response: %s", strings.TrimSpace(line))
	}
	return nil
}
