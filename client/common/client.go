package common

import (
	"encoding/csv"
	"errors"
	"fmt"
	"io"
	"os"
	"os/signal"
	"path/filepath"
	"strconv"
	"strings"
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
	ID             string
	ServerAddress  string
	LoopAmount     int
	LoopPeriod     time.Duration
	BatchMaxAmount int
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

func (c *Client) waitOrStop(sigCh <-chan os.Signal, appClient *application.AppClient) bool {
	select {
	case <-sigCh:
		c.sendShutdownAndFinish(appClient)
		return false
	case <-time.After(c.config.LoopPeriod):
		return true
	}
}

func (c *Client) agencyDatasetPath() string {
	return filepath.Join(".data", fmt.Sprintf("agency-%s.csv", c.config.ID))
}

func (c *Client) loadAgencyDatasetLines() ([]string, error) {
	file, err := os.Open(c.agencyDatasetPath())
	if err != nil {
		return nil, err
	}
	defer func() {
		_ = file.Close()
	}()

	reader := csv.NewReader(file)
	lines := make([]string, 0)
	for {
		record, err := reader.Read()
		if err == io.EOF {
			break
		}
		if err != nil {
			return nil, err
		}
		if len(record) != 5 {
			return nil, fmt.Errorf("invalid bet record format")
		}
		for i := range record {
			record[i] = strings.TrimSpace(record[i])
		}
		lines = append(lines, strings.Join(record, ","))
	}

	return lines, nil
}

func (c *Client) batchSize() int {
	if c.config.BatchMaxAmount <= 0 {
		return 1
	}
	return c.config.BatchMaxAmount
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

	bets, err := c.loadAgencyDatasetLines()
	if err != nil {
		log.Errorf("action: apuesta_enviada | result: fail | client_id: %v | error: %v", c.config.ID, err)
		return
	}

	batchSize := c.batchSize()
	for offset := 0; offset < len(bets); offset += batchSize {
		if c.stopIfSignaled(sigCh, appClient) {
			return
		}

		end := offset + batchSize
		if end > len(bets) {
			end = len(bets)
		}

		if err := appClient.SendBatch(c.config.ID, bets[offset:end]); err != nil {
			if errors.Is(err, application.ErrShutdown) {
				log.Infof("action: receive_shutdown | result: success | client_id: %v", c.config.ID)
				log.Infof("action: loop_finished | result: success | client_id: %v", c.config.ID)
				return
			}
			log.Errorf(
				"action: apuesta_enviada | result: fail | client_id: %v | batch_size: %v | error: %v",
				c.config.ID,
				strconv.Itoa(end-offset),
				err,
			)
			return
		}
	}

	if c.stopIfSignaled(sigCh, appClient) {
		return
	}

	if err := appClient.SendEndAgency(c.config.ID); err != nil {
		if errors.Is(err, application.ErrShutdown) {
			log.Infof("action: receive_shutdown | result: success | client_id: %v", c.config.ID)
			log.Infof("action: loop_finished | result: success | client_id: %v", c.config.ID)
			return
		}
		log.Errorf("action: agencia_finalizada | result: fail | client_id: %v | error: %v", c.config.ID, err)
		return
	}

	if c.stopIfSignaled(sigCh, appClient) {
		return
	}

	winnersCount, err := appClient.GetWinnersCount(c.config.ID)
	if err != nil {
		if errors.Is(err, application.ErrShutdown) {
			log.Infof("action: receive_shutdown | result: success | client_id: %v", c.config.ID)
			log.Infof("action: loop_finished | result: success | client_id: %v", c.config.ID)
			return
		}
		log.Errorf("action: consulta_ganadores | result: fail | client_id: %v | error: %v", c.config.ID, err)
		return
	}

	log.Infof(
		"action: consulta_ganadores | result: success | cant_ganadores: %v",
		winnersCount,
	)

	c.sendShutdownAndFinish(appClient)
}
