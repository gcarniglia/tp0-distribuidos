from common.application.state import ServerState
from common.protocol.messages import (
    Message,
    MSG_BATCH,
    MSG_BET,
    MSG_END_AGENCY,
    MSG_ERROR,
    MSG_ECHO,
    MSG_GET_WINNERS,
    MSG_OK,
    MSG_SHUTDOWN,
)


class AppServer:
    def __init__(self, state: ServerState | None = None):
        self._state = state or ServerState()

    def handle_message(self, connection, message: Message):
        if message.type == MSG_ECHO:
            return [(connection, Message(MSG_OK, message.payload))]
        if message.type == MSG_BET:
            return self._handle_bet(connection, message.payload)
        if message.type == MSG_BATCH:
            return self._handle_batch(connection, message.payload)
        if message.type == MSG_END_AGENCY:
            return self._handle_end_agency(connection, message.payload)
        if message.type == MSG_GET_WINNERS:
            return self._handle_get_winners(connection, message.payload)
        if message.type == MSG_SHUTDOWN:
            return []
        return [(connection, Message(MSG_ERROR, b"unknown_message_type"))]

    def _handle_bet(self, connection, payload: bytes):
        try:
            parsed = self.parse_bet_payload(payload)
            return self.handle_bet(connection, parsed)
        except Exception as exc:
            return [(connection, Message(MSG_ERROR, str(exc).encode("utf-8")))]

    def _handle_batch(self, connection, payload: bytes):
        try:
            parsed = self.parse_batch_payload(payload)
            return self.handle_batch(connection, parsed)
        except Exception as exc:
            return [(connection, Message(MSG_ERROR, str(exc).encode("utf-8")))]

    def _handle_end_agency(self, connection, payload: bytes):
        try:
            parsed = self.parse_end_agency_payload(payload)
            return self.handle_end_agency(connection, parsed)
        except Exception as exc:
            return [(connection, Message(MSG_ERROR, str(exc).encode("utf-8")))]

    def _handle_get_winners(self, connection, payload: bytes):
        try:
            parsed = self.parse_get_winners_payload(payload)
            return self.handle_get_winners(connection, parsed)
        except Exception as exc:
            return [(connection, Message(MSG_ERROR, str(exc).encode("utf-8")))]

    def handle_bet(self, connection, parsed_payload):
        raise NotImplementedError("TODO ej5: implementar BET + store_bets + log apuesta_almacenada")

    def handle_batch(self, connection, parsed_payload):
        raise NotImplementedError("TODO ej6: implementar BATCH atomico + log apuesta_recibida")

    def handle_end_agency(self, connection, parsed_payload):
        raise NotImplementedError("TODO ej7: implementar END_AGENCY + estado de sorteo")

    def handle_get_winners(self, connection, parsed_payload):
        raise NotImplementedError("TODO ej7/ej8: implementar ACK + WINNERS diferido por agencia")

    @staticmethod
    def parse_kv_payload(payload: bytes):
        fields = {}
        for line in payload.decode("utf-8").split("\n"):
            if line.strip() == "":
                continue
            if "=" not in line:
                raise ValueError("invalid_payload_format")
            key, value = line.split("=", 1)
            fields[key.strip()] = value.strip()
        return fields

    def parse_bet_payload(self, payload: bytes):
        fields = self.parse_kv_payload(payload)
        required = ["agency_id", "nombre", "apellido", "documento", "nacimiento", "numero"]
        for key in required:
            if key not in fields:
                raise ValueError(f"missing_field_{key}")
        return fields

    def parse_batch_payload(self, payload: bytes):
        text = payload.decode("utf-8")
        lines = text.split("\n")
        if len(lines) < 3 or lines[2] != "data:":
            raise ValueError("invalid_batch_payload")

        agency_id = lines[0].split("=", 1)[1].strip()
        count = int(lines[1].split("=", 1)[1].strip())
        data_lines = [line for line in lines[3:] if line.strip() != ""]
        if count != len(data_lines):
            raise ValueError("batch_count_mismatch")

        return {
            "agency_id": agency_id,
            "count": count,
            "csv_lines": data_lines,
        }

    def parse_end_agency_payload(self, payload: bytes):
        fields = self.parse_kv_payload(payload)
        if "agency_id" not in fields:
            raise ValueError("missing_field_agency_id")
        return {"agency_id": int(fields["agency_id"]) }

    def parse_get_winners_payload(self, payload: bytes):
        fields = self.parse_kv_payload(payload)
        if "agency_id" not in fields:
            raise ValueError("missing_field_agency_id")
        return {"agency_id": int(fields["agency_id"]) }

    @staticmethod
    def ok(connection):
        return [(connection, Message(MSG_OK, b""))]
