from dataclasses import dataclass


MSG_BET = "BET"
MSG_BATCH = "BATCH"
MSG_END_AGENCY = "END_AGENCY"
MSG_GET_WINNERS = "GET_WINNERS"
MSG_WINNERS = "WINNERS"
MSG_OK = "OK"
MSG_ERROR = "ERROR"
MSG_SHUTDOWN = "SHUTDOWN"
MSG_ECHO = "ECHO"


@dataclass
class Message:
    type: str
    payload: bytes
