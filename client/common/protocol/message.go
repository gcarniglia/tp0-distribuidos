package protocol

type MessageType string

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

type Message struct {
	Type    MessageType
	Payload []byte
}
