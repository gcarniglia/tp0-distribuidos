package application

import (
	"errors"
	"fmt"

	"github.com/op/go-logging"
)

var log = logging.MustGetLogger("log")

func buildEchoMessage(msgID int, clientID string) string {
	return fmt.Sprintf("[CLIENT %v] Message N°%v", clientID, msgID)
}

func (a *AppClient) ExecuteEcho(msgID int, clientID string) (string, error) {
	message := buildEchoMessage(msgID, clientID)
	return a.SendEcho(message)
}

func (a *AppClient) ProcessEchoMessage(msgID int, clientID string) bool {
	response, err := a.ExecuteEcho(msgID, clientID)
	if err == nil {
		log.Infof("action: receive_message | result: success | client_id: %v | msg: %v",
			clientID,
			response,
		)
		return true
	}

	if errors.Is(err, ErrShutdown) {
		log.Infof("action: receive_shutdown | result: success | client_id: %v", clientID)
		log.Infof("action: loop_finished | result: success | client_id: %v", clientID)
		return false
	}

	log.Errorf("action: receive_message | result: fail | client_id: %v | error: %v",
		clientID,
		err,
	)
	return false
}
