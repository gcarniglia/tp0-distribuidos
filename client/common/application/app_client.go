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
	codec *protocol.Codec
}

var ErrShutdown = errors.New("shutdown received")

func NewAppClient(conn *transport.Conn, codec *protocol.Codec) *AppClient {
	return &AppClient{conn: conn, codec: codec}
}

func (a *AppClient) SendAndReceive(msg protocol.Message) (protocol.Message, error) {
	frame, err := a.codec.Encode(msg)
	if err != nil {
		return protocol.Message{}, err
	}
	if err := a.conn.WriteAll(frame); err != nil {
		return protocol.Message{}, err
	}
	response, err := a.codec.DecodeFrom(a.conn)
	if err != nil {
		return protocol.Message{}, err
	}
	if response.Type == protocol.MsgShutdown {
		return response, ErrShutdown
	}
	return response, nil
}

func (a *AppClient) SendEcho(text string) (string, error) {
	response, err := a.SendAndReceive(protocol.Message{Type: protocol.MsgEcho, Payload: []byte(text)})
	if err != nil {
		return "", err
	}
	if response.Type == protocol.MsgError {
		return "", fmt.Errorf("server returned error: %s", string(response.Payload))
	}
	return string(response.Payload), nil
}

func (a *AppClient) NotifyEndAgency(agencyID string) error {
	payload := fmt.Sprintf("agency_id=%s", agencyID)
	response, err := a.SendAndReceive(protocol.Message{Type: protocol.MsgENDAgency, Payload: []byte(payload)})
	if err != nil {
		return err
	}
	if response.Type != protocol.MsgOK {
		return fmt.Errorf("unexpected response type: %s", response.Type)
	}
	return nil
}

func (a *AppClient) SendShutdown() error {
	frame, err := a.codec.Encode(protocol.Message{Type: protocol.MsgShutdown, Payload: []byte{}})
	if err != nil {
		return err
	}
	return a.conn.WriteAll(frame)
}
