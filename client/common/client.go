package common

import (
	"os"
	"os/signal"
	"syscall"

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
}

// Client Entity
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

func (c *Client) sendShutdownAndFinish(appClient *application.AppClient) {
	log.Infof("action: send_shutdown | result: in_progress | mode: unilateral | client_id: %v", c.config.ID)
	if err := appClient.SendShutdown(); err != nil {
		log.Errorf("action: send_shutdown | result: fail | client_id: %v | error: %v", c.config.ID, err)
		log.Infof("action: loop_finished | result: fail | mode: unilateral_shutdown_failed | client_id: %v", c.config.ID)
		return
	}
	log.Infof("action: send_shutdown | result: success | mode: unilateral | client_id: %v", c.config.ID)
	log.Infof("action: loop_finished | result: success | mode: unilateral_shutdown_sent | client_id: %v", c.config.ID)
}

func (c *Client) stopIfSignaled(sigCh <-chan os.Signal, appClient *application.AppClient) bool {
	select {
	case <-sigCh:
		log.Infof("action: sigterm_received | result: success | client_id: %v", c.config.ID)
		c.sendShutdownAndFinish(appClient)
		return true
	default:
		return false
	}
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
		log.Infof("action: close_connection | result: in_progress | client_id: %v", c.config.ID)
		_ = conn.Close()
		log.Infof("action: close_connection | result: success | client_id: %v", c.config.ID)
	}()

	appClient := application.NewAppClient(conn, codec)

	// There is an autoincremental msgID to identify every message sent
	// Messages if the message amount threshold has not been surpassed
	for msgID := 1; msgID <= c.config.LoopAmount; msgID++ {
		if c.stopIfSignaled(sigCh, appClient) {
			return
		}

		if !appClient.ProcessEchoMessage(msgID, c.config.ID) {
			return
		}

	}
	c.sendShutdownAndFinish(appClient)
}
