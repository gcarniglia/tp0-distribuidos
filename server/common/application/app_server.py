import logging
import threading

from common.protocol.smile_message import (
    SmileMessage, SmileType
)
from common.utils import Bet, store_bets


class AppServer:
    def __init__(self):
        self._storage_lock = threading.Lock()

    def handle_message(self, connection, message: SmileMessage):
        if message.type == SmileType.ECHO:
            return self.ok(connection, message.payload), True, None
        if message.type == SmileType.BET:
            try:
                bet = self._decode_bet_payload(message.payload)
                with self._storage_lock:
                    store_bets([bet])
                logging.info(
                    "action: apuesta_almacenada | result: success | dni: %s | numero: %s",
                    bet.document,
                    bet.number,
                )
                return self.ok(connection, b""), True, None
            except ValueError as exc:
                return [(connection, SmileMessage(SmileType.ERROR, str(exc).encode("utf-8")))], True, None
        if message.type == SmileType.BATCH:
            bet_count = self._extract_batch_count(message.payload)
            try:
                bets = self._decode_batch_payload(message.payload)
                with self._storage_lock:
                    store_bets(bets)
                logging.info(
                    "action: apuesta_recibida | result: success | cantidad: %s",
                    len(bets),
                )
                return self.ok(connection, b""), True, None
            except ValueError as exc:
                logging.info(
                    "action: apuesta_recibida | result: fail | cantidad: %s",
                    bet_count,
                )
                return [(connection, SmileMessage(SmileType.ERROR, str(exc).encode("utf-8")))], True, None
        if message.type == SmileType.END_AGENCY:
            return [], True, None
        if message.type == SmileType.GET_WINNERS:
            return [], True, None
        if message.type == SmileType.SHUTDOWN:
            return self.shutdown(connection)
        return [(connection, SmileMessage(SmileType.ERROR, b"unknown_message_type"))], True, None

    @staticmethod
    def shutdown(connection):
        if connection.is_open():
            connection.close()
        return [], False, "protocol_shutdown"

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

    @staticmethod
    def _extract_batch_count(payload: bytes) -> int:
        try:
            text = payload.decode("utf-8")
        except UnicodeDecodeError:
            return 0

        for line in text.split("\n"):
            if line.startswith("count="):
                try:
                    return int(line.split("=", 1)[1])
                except ValueError:
                    return 0
        return 0

    @staticmethod
    def _decode_batch_payload(payload: bytes) -> list[Bet]:
        try:
            text = payload.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError("invalid_batch_payload_encoding") from exc

        lines = text.split("\n")
        if len(lines) < 3:
            raise ValueError("invalid_batch_payload_format")

        if not lines[0].startswith("agency_id="):
            raise ValueError("missing_batch_field_agency_id")
        if not lines[1].startswith("count="):
            raise ValueError("missing_batch_field_count")
        if lines[2] != "data:":
            raise ValueError("missing_batch_field_data")

        agency_id = lines[0].split("=", 1)[1]
        try:
            count = int(lines[1].split("=", 1)[1])
        except ValueError as exc:
            raise ValueError("invalid_batch_count") from exc

        if agency_id == "":
            raise ValueError("missing_batch_field_agency_id")
        if count < 0:
            raise ValueError("invalid_batch_count")

        data_lines = [line for line in lines[3:] if line != ""]
        if len(data_lines) != count:
            raise ValueError("batch_count_mismatch")

        bets = []
        for data_line in data_lines:
            fields = data_line.split(",")
            if len(fields) != 5:
                raise ValueError("invalid_batch_bet_format")

            first_name = fields[0].strip()
            last_name = fields[1].strip()
            document = fields[2].strip()
            birthdate = fields[3].strip()
            number = fields[4].strip()

            if first_name == "" or last_name == "" or document == "" or birthdate == "" or number == "":
                raise ValueError("invalid_batch_bet_values")

            try:
                bets.append(
                    Bet(
                        agency=agency_id,
                        first_name=first_name,
                        last_name=last_name,
                        document=document,
                        birthdate=birthdate,
                        number=number,
                    )
                )
            except (TypeError, ValueError) as exc:
                raise ValueError("invalid_batch_bet_values") from exc

        return bets
