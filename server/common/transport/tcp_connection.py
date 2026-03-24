import socket


class TcpConnection:
    def __init__(self, sock: socket.socket):
        self._sock = sock

    def send_all(self, data: bytes) -> None:
        self._sock.sendall(data)

    def read_exactly(self, n: int) -> bytes:
        chunks = []
        remaining = n
        while remaining > 0:
            chunk = self._sock.recv(remaining)
            if not chunk:
                raise EOFError("unexpected EOF while reading payload")
            chunks.append(chunk)
            remaining -= len(chunk)
        return b"".join(chunks)

    def read_until_header_terminator(self) -> bytes:
        buffer = bytearray()
        while True:
            chunk = self._sock.recv(1)
            if not chunk:
                raise EOFError("unexpected EOF while reading header")
            buffer.extend(chunk)
            if len(buffer) >= 3 and buffer[-3:] == b":(\n":
                return bytes(buffer)
            if len(buffer) > 4096:
                raise ValueError("header too large")

    def peer_ip(self) -> str:
        return self._sock.getpeername()[0]

    def close(self) -> None:
        self._sock.close()

    def settimeout(self, value: float) -> None:
        self._sock.settimeout(value)
