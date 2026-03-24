package application

import (
	"errors"
	"fmt"

	"github.com/gcarniglia/tp0-distribuidos/client/common/protocol"
	"github.com/gcarniglia/tp0-distribuidos/client/common/transport"
)

type Bet struct {
	AgencyID   string
	Nombre     string
	Apellido   string
	Documento  string
	Nacimiento string
	Numero     string
}

type AppClient struct {
	conn  *transport.Conn
	codec *protocol.SmileProtocol
}

var ErrShutdown = errors.New("shutdown received")

func NewAppClient(conn *transport.Conn, codec *protocol.SmileProtocol) *AppClient {
	return &AppClient{conn: conn, codec: codec}
}

func (a *AppClient) SendAndReceive(msg protocol.SmileMessage) (protocol.SmileMessage, error) {
	frame, err := a.codec.Encode(msg)
	if err != nil {
		return protocol.SmileMessage{}, err
	}
	if err := a.conn.WriteAll(frame); err != nil {
		return protocol.SmileMessage{}, err
	}
	response, err := a.codec.DecodeFrom(a.conn)
	if err != nil {
		return protocol.SmileMessage{}, err
	}
	if response.Type == protocol.MsgShutdown {
		return response, ErrShutdown
	}
	return response, nil
}

func (a *AppClient) SendEcho(text string) (string, error) {
	response, err := a.SendAndReceive(protocol.SmileMessage{Type: protocol.MsgEcho, Payload: []byte(text)})
	if err != nil {
		return "", err
	}
	if response.Type == protocol.MsgError {
		return "", fmt.Errorf("server returned error: %s", string(response.Payload))
	}
	return string(response.Payload), nil
}

func (a *AppClient) SendShutdown() error {
	frame, err := a.codec.Encode(protocol.SmileMessage{Type: protocol.MsgShutdown, Payload: []byte{}})
	if err != nil {
		return err
	}
	return a.conn.WriteAll(frame)
}
