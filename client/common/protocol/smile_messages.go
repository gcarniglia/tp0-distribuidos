package protocol

type MessageType string

// Definición de los tipos de mensaje utilizados en el Smile Protocol
const (
	MsgBET        MessageType = "BET"
	MsgBATCH      MessageType = "BATCH"
	MsgENDAgency  MessageType = "END_AGENCY"
	MsgGetWinners MessageType = "GET_WINNERS"
	MsgWinners    MessageType = "WINNERS"
	MsgOK         MessageType = "OK"
	MsgError      MessageType = "ERROR"
	MsgShutdown   MessageType = "SHUTDOWN"
	MsgEcho       MessageType = "ECHO"
)

// Definición de la estructura de mensaje utilizada en el Smile Protocol
type Message struct {
	Type    MessageType
	Payload []byte
}
