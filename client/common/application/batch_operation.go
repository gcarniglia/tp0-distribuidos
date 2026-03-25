package application

import (
	"fmt"
	"strconv"
	"strings"

	"github.com/gcarniglia/tp0-distribuidos/client/common/protocol"
)

func SerializeBatchPayload(agencyID string, bets []string) string {
	var builder strings.Builder
	builder.WriteString("agency_id=")
	builder.WriteString(agencyID)
	builder.WriteString("\ncount=")
	builder.WriteString(strconv.Itoa(len(bets)))
	builder.WriteString("\ndata:\n")
	for i, line := range bets {
		builder.WriteString(line)
		if i < len(bets)-1 {
			builder.WriteByte('\n')
		}
	}
	return builder.String()
}

func (a *AppClient) SendBatch(agencyID string, bets []string) error {
	payload := SerializeBatchPayload(agencyID, bets)
	response, err := a.SendAndReceive(protocol.SmileMessage{Type: protocol.MsgBATCH, Payload: []byte(payload)})
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
