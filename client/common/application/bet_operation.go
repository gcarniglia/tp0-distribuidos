package application

import (
	"fmt"
	"strings"

	"github.com/gcarniglia/tp0-distribuidos/client/common/protocol"
)

func SerializeBetPayload(bet Bet) string {
	return fmt.Sprintf(
		"agency_id=%s\nnombre=%s\napellido=%s\ndocumento=%s\nnacimiento=%s\nnumero=%s",
		bet.AgencyID,
		bet.Nombre,
		bet.Apellido,
		bet.Documento,
		bet.Nacimiento,
		bet.Numero,
	)
}

func (a *AppClient) SendBet(bet Bet) error {
	payload := SerializeBetPayload(bet)
	response, err := a.SendAndReceive(protocol.SmileMessage{Type: protocol.MsgBET, Payload: []byte(payload)})
	if err != nil {
		return err
	}

	if response.Type == protocol.MsgError {
		return fmt.Errorf("server returned error: %s", strings.TrimSpace(string(response.Payload)))
	}

	if response.Type != protocol.MsgOK {
		return fmt.Errorf("unexpected response type: %s", response.Type)
	}

	return nil
}
