package transport

import (
	"bufio"
	"fmt"
	"io"
	"net"
)

type Conn struct {
	netConn net.Conn
	reader  *bufio.Reader
}

func Dial(address string) (*Conn, error) {
	netConn, err := net.Dial("tcp", address)
	if err != nil {
		return nil, err
	}
	return &Conn{netConn: netConn, reader: bufio.NewReader(netConn)}, nil
}

func (c *Conn) WriteAll(data []byte) error {
	total := 0
	for total < len(data) {
		n, err := c.netConn.Write(data[total:])
		if err != nil {
			return err
		}
		if n == 0 {
			return io.ErrUnexpectedEOF
		}
		total += n
	}
	return nil
}

func (c *Conn) ReadExactly(n int) ([]byte, error) {
	buf := make([]byte, n)
	if _, err := io.ReadFull(c.reader, buf); err != nil {
		return nil, err
	}
	return buf, nil
}

func (c *Conn) ReadUntilHeaderTerminator() ([]byte, error) {
	buf := make([]byte, 0, 64)
	for {
		b, err := c.reader.ReadByte()
		if err != nil {
			return nil, err
		}
		buf = append(buf, b)
		size := len(buf)
		if size >= 3 && buf[size-3] == ':' && buf[size-2] == '(' && buf[size-1] == '\n' {
			return buf, nil
		}
		if len(buf) > 4096 {
			return nil, fmt.Errorf("header too large")
		}
	}
}

func (c *Conn) Close() error {
	if c == nil || c.netConn == nil {
		return nil
	}
	return c.netConn.Close()
}
