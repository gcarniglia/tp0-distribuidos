package common

import (
	"errors"
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
	Nombre        string
	Apellido      string
	Documento     string
	Nacimiento    string
	Numero        string
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
	if err := appClient.SendShutdown(); err != nil {
		log.Errorf("action: send_shutdown | result: fail | client_id: %v | error: %v", c.config.ID, err)
	}
	log.Infof("action: loop_finished | result: success | client_id: %v", c.config.ID)
}

func (c *Client) stopIfSignaled(sigCh <-chan os.Signal, appClient *application.AppClient) bool {
	select {
	case <-sigCh:
		c.sendShutdownAndFinish(appClient)
		return true
	default:
		return false
	}
}

func (c *Client) buildBet() application.Bet {
	return application.Bet{
		AgencyID:   c.config.ID,
		Nombre:     c.config.Nombre,
		Apellido:   c.config.Apellido,
		Documento:  c.config.Documento,
		Nacimiento: c.config.Nacimiento,
		Numero:     c.config.Numero,
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
		_ = conn.Close()
	}()

	appClient := application.NewAppClient(conn, codec)

	if c.stopIfSignaled(sigCh, appClient) {
		return
	}

	bet := c.buildBet()
	if err := appClient.SendBet(bet); err != nil {
		if errors.Is(err, application.ErrShutdown) {
			log.Infof("action: receive_shutdown | result: success | client_id: %v", c.config.ID)
			log.Infof("action: loop_finished | result: success | client_id: %v", c.config.ID)
			return
		}
		log.Errorf("action: apuesta_enviada | result: fail | dni: %v | numero: %v | error: %v", bet.Documento, bet.Numero, err)
		return
	}

	log.Infof("action: apuesta_enviada | result: success | dni: %v | numero: %v", bet.Documento, bet.Numero)
	c.sendShutdownAndFinish(appClient)
}
