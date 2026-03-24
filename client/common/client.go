package common

import (
	"errors"
	"fmt"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/op/go-logging"

	"github.com/gcarniglia/tp0-distribuidos/client/common/application"
	"github.com/gcarniglia/tp0-distribuidos/client/common/protocol"
	"github.com/gcarniglia/tp0-distribuidos/client/common/transport"
)

var log = logging.MustGetLogger("log")

// ClientConfig Configuration used by the client
type ClientConfig struct {
	ID            string
	ServerAddress string
	LoopAmount    int
	LoopPeriod    time.Duration
}

// Client Entity that encapsulates how
type Client struct {
	config ClientConfig
}

// NewClient Initializes a new client receiving the configuration
// as a parameter
func NewClient(config ClientConfig) *Client {
	client := &Client{
		config: config,
	}
	return client
}

// CreateClientSocket Initializes client socket. In case of
// failure, error is printed in stdout/stderr and exit 1
// is returned
func (c *Client) createClientSocket() (*transport.Conn, error) {
	conn, err := transport.Dial(c.config.ServerAddress)
	if err != nil {
		log.Criticalf(
			"action: connect | result: fail | client_id: %v | error: %v",
			c.config.ID,
			err,
		)
		return nil, err
	}
	return conn, nil
}

// StartClientLoop Send messages to the client until some time threshold is met
func (c *Client) StartClientLoop() {
	sigCh := make(chan os.Signal, 1)
	signal.Notify(sigCh, syscall.SIGTERM)
	defer signal.Stop(sigCh)

	codec := protocol.NewCodec()
	conn, err := c.createClientSocket()
	if err != nil {
		return
	}
	defer func() {
		_ = conn.Close()
	}()

	appClient := application.NewAppClient(conn, codec)

	// There is an autoincremental msgID to identify every message sent
	// Messages if the message amount threshold has not been surpassed
	for msgID := 1; msgID <= c.config.LoopAmount; msgID++ {
		select {
		case <-sigCh:
			if err := appClient.SendShutdown(); err != nil {
				log.Errorf("action: send_shutdown | result: fail | client_id: %v | error: %v", c.config.ID, err)
			}
			log.Infof("action: loop_finished | result: success | client_id: %v", c.config.ID)
			return
		default:
		}

		message := fmt.Sprintf("[CLIENT %v] Message N°%v", c.config.ID, msgID)
		response, err := appClient.SendEcho(message)
		if err == nil {
			log.Infof("action: receive_message | result: success | client_id: %v | msg: %v",
				c.config.ID,
				response,
			)
		} else {
			if errors.Is(err, application.ErrShutdown) {
				log.Infof("action: receive_shutdown | result: success | client_id: %v", c.config.ID)
				log.Infof("action: loop_finished | result: success | client_id: %v", c.config.ID)
				return
			}
			log.Errorf("action: receive_message | result: fail | client_id: %v | error: %v",
				c.config.ID,
				err,
			)
			return
		}

		// Wait a time between sending one message and the next one
		select {
		case <-sigCh:
			if err := appClient.SendShutdown(); err != nil {
				log.Errorf("action: send_shutdown | result: fail | client_id: %v | error: %v", c.config.ID, err)
			}
			log.Infof("action: loop_finished | result: success | client_id: %v", c.config.ID)
			return
		case <-time.After(c.config.LoopPeriod):
		}

	}
	if err := appClient.SendShutdown(); err != nil {
		log.Errorf("action: send_shutdown | result: fail | client_id: %v | error: %v", c.config.ID, err)
	}
	log.Infof("action: loop_finished | result: success | client_id: %v", c.config.ID)
}
