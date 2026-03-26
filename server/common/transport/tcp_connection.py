import socket

'''Modula que representa una conexión TCP con un cliente'''
class TcpConnection:
    def __init__(self, sock: socket.socket):
        self._socket = sock
        self._closed = False

    '''Envía todos los bytes del mensaje a través de la conexión TCP'''
    def send_all(self, data: bytes) -> None:
        self._socket.sendall(data)

    '''Lee exactamente n bytes del mensaje a través de la conexión TCP
    Se usa para la lectura del payload, luego de haber leído el header'''
    def read_exactly(self, n: int) -> bytes:
        chunks = []
        remaining = n
        while remaining > 0:
            chunk = self._socket.recv(remaining)
            if not chunk:
                raise EOFError("unexpected EOF while reading payload")
            chunks.append(chunk)
            remaining -= len(chunk)
        return b"".join(chunks)

    '''Lee byte a byte hasta encontrar el terminador de header del Smile Protocol
    ":(\n", retornando el header completo incluyendo el terminador'''
    def read_until_header_terminator(self) -> bytes:
        buffer = bytearray()
        while True:
            chunk = self._socket.recv(1)
            if not chunk:
                raise EOFError("unexpected EOF while reading header")
            buffer.extend(chunk)
            if len(buffer) >= 3 and buffer[-3:] == b":(\n":
                return bytes(buffer)
            if len(buffer) > 4096:
                raise ValueError("header too large")


    def peer_ip(self) -> str:
        return self._socket.getpeername()[0]

    ''' Cierra la conexión TCP con el cliente'''
    def close(self) -> None:
        if self._closed:
            return
        self._socket.close()
        self._closed = True

    def is_open(self) -> bool:
        if self._closed:
            return False
        try:
            return self._socket.fileno() != -1
        except OSError:
            return False

    def settimeout(self, value: float) -> None:
        self._socket.settimeout(value)
