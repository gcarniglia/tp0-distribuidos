import logging

from common.application.state import ServerState
from common.protocol.smile_message import (
    SmileMessage, SmileType
)
from common.utils import Bet, store_bets


class AppServer:
    def __init__(self, state: ServerState | None = None):
        self._state = state or ServerState()

    def handle_message(self, connection, message: SmileMessage):
        if message.type == SmileType.ECHO:
            return self.ok(connection, message.payload)
        if message.type == SmileType.BET:
            try:
                bet = self._decode_bet_payload(message.payload)
                store_bets([bet])
                logging.info(
                    "action: apuesta_almacenada | result: success | dni: %s | numero: %s",
                    bet.document,
                    bet.number,
                )
                return self.ok(connection, b"")
            except ValueError as exc:
                return [(connection, SmileMessage(SmileType.ERROR, str(exc).encode("utf-8")))]
        if message.type == SmileType.BATCH:
            return []
        if message.type == SmileType.END_AGENCY:
            return []
        if message.type == SmileType.GET_WINNERS:
            return []
        if message.type == SmileType.SHUTDOWN:
            return []
        return [(connection, SmileMessage(SmileType.ERROR, b"unknown_message_type"))]

    @staticmethod
    def ok(connection,payload):
        return [(connection, SmileMessage(SmileType.OK, payload))]

    @staticmethod
    def _decode_bet_payload(payload: bytes) -> Bet:
        try:
            text = payload.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError("invalid_bet_payload_encoding") from exc

        fields = {}
        for line in text.split("\n"):
            if line == "":
                continue
            if "=" not in line:
                raise ValueError("invalid_bet_payload_format")
            key, value = line.split("=", 1)
            fields[key] = value

        required_fields = ["agency_id", "nombre", "apellido", "documento", "nacimiento", "numero"]
        for field_name in required_fields:
            if field_name not in fields or fields[field_name] == "":
                raise ValueError(f"missing_bet_field_{field_name}")

        try:
            return Bet(
                agency=fields["agency_id"],
                first_name=fields["nombre"],
                last_name=fields["apellido"],
                document=fields["documento"],
                birthdate=fields["nacimiento"],
                number=fields["numero"],
            )
        except (TypeError, ValueError) as exc:
            raise ValueError("invalid_bet_payload_values") from exc
