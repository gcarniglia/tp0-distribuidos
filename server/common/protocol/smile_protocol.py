from server.common.protocol.smile_message import SmileMessage, SmileType
from server.common.protocol.constants import MAX_PAYLOAD_LEN
from server.common.protocol.smile_errors import SmileError, PayloadTooLargeError




'''Modulo que implementa el Smile Protocol, 
encargado de codificar y decodificar mensajes'''
class SmileProtocol:
    def encode(self, message: SmileMessage) -> bytes:
        if len(message.payload) > MAX_PAYLOAD_LEN:
            raise PayloadTooLargeError(len(message.payload))
        header = f":){message.type.value} {len(message.payload)}:(\n".encode("utf-8")
        return header + message.payload

    def decode_from(self, connection) -> SmileMessage:
        header = connection.read_until_header_terminator()
        if not header.startswith(b":)") or not header.endswith(b":(\n"):
            raise SmileError("invalid frame header")

        body = header[2:-3].decode("utf-8")
        parts = body.split(" ")
        if len(parts) != 2:
            raise SmileError("invalid frame header body")

        msg_type = parts[0]
        try:
            payload_len = int(parts[1])
        except ValueError as exc:
            raise SmileError("invalid payload length") from exc

        if payload_len < 0:
            raise SmileError("invalid payload length")

        if payload_len > MAX_PAYLOAD_LEN:
            raise PayloadTooLargeError(payload_len)

        payload = connection.read_exactly(payload_len)
        return SmileMessage(type=SmileType(msg_type), payload=payload)
