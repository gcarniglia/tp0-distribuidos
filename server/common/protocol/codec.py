from common.protocol.messages import Message

MAX_PAYLOAD_LEN = 8192


class ProtocolError(Exception):
    pass


class PayloadTooLargeError(ProtocolError):
    def __init__(self, payload_len: int):
        super().__init__(f"payload length exceeds max allowed: {payload_len}")
        self.payload_len = payload_len


class Codec:
    def encode(self, message: Message) -> bytes:
        if len(message.payload) > MAX_PAYLOAD_LEN:
            raise PayloadTooLargeError(len(message.payload))
        header = f":){message.type} {len(message.payload)}:(\n".encode("utf-8")
        return header + message.payload

    def decode_from(self, connection) -> Message:
        header = connection.read_until_header_terminator()
        if not header.startswith(b":)") or not header.endswith(b":(\n"):
            raise ProtocolError("invalid frame header")

        body = header[2:-3].decode("utf-8")
        parts = body.split(" ")
        if len(parts) != 2:
            raise ProtocolError("invalid frame header body")

        msg_type = parts[0]
        try:
            payload_len = int(parts[1])
        except ValueError as exc:
            raise ProtocolError("invalid payload length") from exc

        if payload_len < 0:
            raise ProtocolError("invalid payload length")

        if payload_len > MAX_PAYLOAD_LEN:
            raise PayloadTooLargeError(payload_len)

        payload = connection.read_exactly(payload_len)
        return Message(type=msg_type, payload=payload)
