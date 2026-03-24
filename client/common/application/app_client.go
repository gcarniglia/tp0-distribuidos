package application

import (
	"fmt"
	"strings"

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
	return a.codec.DecodeFrom(a.conn)
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

func (a *AppClient) SendBet(bet Bet) error {
	payload := fmt.Sprintf("agency_id=%s\nnombre=%s\napellido=%s\ndocumento=%s\nnacimiento=%s\nnumero=%s",
		bet.AgencyID, bet.Nombre, bet.Apellido, bet.Documento, bet.Nacimiento, bet.Numero)
	response, err := a.SendAndReceive(protocol.Message{Type: protocol.MsgBET, Payload: []byte(payload)})
	if err != nil {
		return err
	}
	if response.Type != protocol.MsgOK {
		return fmt.Errorf("unexpected response type: %s", response.Type)
	}
	return nil
}

func (a *AppClient) SendBatch(agencyID string, csvLines []string) error {
	payload := fmt.Sprintf("agency_id=%s\ncount=%d\ndata:\n%s", agencyID, len(csvLines), strings.Join(csvLines, "\n"))
	response, err := a.SendAndReceive(protocol.Message{Type: protocol.MsgBATCH, Payload: []byte(payload)})
	if err != nil {
		return err
	}
	if response.Type != protocol.MsgOK {
		return fmt.Errorf("unexpected response type: %s", response.Type)
	}
	return nil
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

func (a *AppClient) RequestWinners(agencyID string) ([]string, error) {
	payload := fmt.Sprintf("agency_id=%s", agencyID)
	ack, err := a.SendAndReceive(protocol.Message{Type: protocol.MsgGetWinners, Payload: []byte(payload)})
	if err != nil {
		return nil, err
	}
	if ack.Type != protocol.MsgOK {
		return nil, fmt.Errorf("unexpected ack response type: %s", ack.Type)
	}
	winnersMsg, err := a.codec.DecodeFrom(a.conn)
	if err != nil {
		return nil, err
	}
	if winnersMsg.Type != protocol.MsgWinners {
		return nil, fmt.Errorf("unexpected winners response type: %s", winnersMsg.Type)
	}
	lines := strings.Split(string(winnersMsg.Payload), "\n")
	winners := make([]string, 0)
	inData := false
	for _, line := range lines {
		if line == "data:" {
			inData = true
			continue
		}
		if inData && strings.TrimSpace(line) != "" {
			winners = append(winners, strings.TrimSpace(line))
		}
	}
	return winners, nil
}

func (a *AppClient) SendShutdown() error {
	frame, err := a.codec.Encode(protocol.Message{Type: protocol.MsgShutdown, Payload: []byte{}})
	if err != nil {
		return err
	}
	return a.conn.WriteAll(frame)
}
