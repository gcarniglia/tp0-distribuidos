package protocol

type SmileType string

// Definición de los tipos de mensaje utilizados en el Smile Protocol
const (
	MsgBET        SmileType = "BET"
	MsgBATCH      SmileType = "BATCH"
	MsgENDAgency  SmileType = "END_AGENCY"
	MsgGetWinners SmileType = "GET_WINNERS"
	MsgWinners    SmileType = "WINNERS"
	MsgOK         SmileType = "OK"
	MsgError      SmileType = "ERROR"
	MsgShutdown   SmileType = "SHUTDOWN"
	MsgEcho       SmileType = "ECHO"
)

// Definición de la estructura de mensaje utilizada en el Smile Protocol
type SmileMessage struct {
	Type    SmileType
	Payload []byte
}
