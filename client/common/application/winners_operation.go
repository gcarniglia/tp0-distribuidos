package application

import (
	"fmt"
	"strconv"
	"strings"

	"github.com/gcarniglia/tp0-distribuidos/client/common/protocol"
)

func serializeAgencyPayload(agencyID string) string {
	return fmt.Sprintf("agency_id=%s", agencyID)
}

func (a *AppClient) SendEndAgency(agencyID string) error {
	payload := serializeAgencyPayload(agencyID)
	response, err := a.SendAndReceive(protocol.SmileMessage{Type: protocol.MsgENDAgency, Payload: []byte(payload)})
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

func (a *AppClient) GetWinnersCount(agencyID string) (int, error) {
	payload := serializeAgencyPayload(agencyID)
	response, err := a.SendAndReceive(protocol.SmileMessage{Type: protocol.MsgGetWinners, Payload: []byte(payload)})
	if err != nil {
		return 0, err
	}

	if response.Type == protocol.MsgError {
		return 0, fmt.Errorf("server returned error: %s", strings.TrimSpace(string(response.Payload)))
	}

	if response.Type != protocol.MsgWinners {
		return 0, fmt.Errorf("unexpected response type: %s", response.Type)
	}

	count, err := parseWinnersCount(response.Payload)
	if err != nil {
		return 0, err
	}

	return count, nil
}

func parseWinnersCount(payload []byte) (int, error) {
	text := string(payload)
	for _, line := range strings.Split(text, "\n") {
		if strings.HasPrefix(line, "count=") {
			countText := strings.TrimSpace(strings.TrimPrefix(line, "count="))
			count, err := strconv.Atoi(countText)
			if err != nil {
				return 0, fmt.Errorf("invalid winners count")
			}
			if count < 0 {
				return 0, fmt.Errorf("invalid winners count")
			}
			return count, nil
		}
	}
	return 0, fmt.Errorf("missing winners count")
}
