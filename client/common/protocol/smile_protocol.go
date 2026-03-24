package protocol

import (
	"fmt"
	"strconv"
	"strings"

	"github.com/gcarniglia/tp0-distribuidos/client/common/transport"
)

// Modulo que implementa el Smile Protocol,
// encargado de codificar y decodificar mensajes
type SmileProtocol struct{}

func NewCodec() *SmileProtocol {
	return &SmileProtocol{}
}

func (c *SmileProtocol) Encode(msg SmileMessage) ([]byte, error) {
	if len(msg.Payload) > MaxPayloadLen {
		return nil, fmt.Errorf("payload too large: %d", len(msg.Payload))
	}
	header := fmt.Sprintf(":)%s %d:(\n", msg.Type, len(msg.Payload))
	buffer := make([]byte, 0, len(header)+len(msg.Payload))
	buffer = append(buffer, []byte(header)...)
	buffer = append(buffer, msg.Payload...)
	return buffer, nil
}

func (c *SmileProtocol) DecodeFrom(conn *transport.Conn) (SmileMessage, error) {
	headerBytes, err := conn.ReadUntilHeaderTerminator()
	if err != nil {
		return SmileMessage{}, err
	}
	header := string(headerBytes)
	if !strings.HasPrefix(header, ":)") || !strings.HasSuffix(header, ":(\n") {
		return SmileMessage{}, fmt.Errorf("invalid frame header")
	}

	headerBody := strings.TrimSuffix(strings.TrimPrefix(header, ":)"), ":(\n")
	parts := strings.Split(headerBody, " ")
	if len(parts) != 2 {
		return SmileMessage{}, fmt.Errorf("invalid frame header body")
	}

	msgType := parts[0]
	payloadLen, err := strconv.Atoi(parts[1])
	if err != nil || payloadLen < 0 {
		return SmileMessage{}, fmt.Errorf("invalid payload length")
	}
	if payloadLen > MaxPayloadLen {
		return SmileMessage{}, fmt.Errorf("payload length exceeds max allowed")
	}

	payload, err := conn.ReadExactly(payloadLen)
	if err != nil {
		return SmileMessage{}, err
	}

	return SmileMessage{Type: SmileType(msgType), Payload: payload}, nil
}
