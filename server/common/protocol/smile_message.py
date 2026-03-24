from dataclasses import dataclass
from enum import Enum


'''Definición de los tipos de mensaje utilizados en el Smile Protocol'''
class SmileType(Enum):
    BET = "BET"
    BATCH = "BATCH"
    END_AGENCY = "END_AGENCY"
    GET_WINNERS = "GET_WINNERS"
    WINNERS = "WINNERS"
    OK = "OK"
    ERROR = "ERROR"
    SHUTDOWN = "SHUTDOWN"
    ECHO = "ECHO"


'''Definición de la estructura de mensaje utilizada en el Smile Protocol'''
@dataclass
class SmileMessage:
    type: SmileType
    payload: bytes
