import socket
from common.transport.tcp_connection import TcpConnection


class TcpServer:
    def __init__(self, port: int, listen_backlog: int):
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server_socket.bind(("", port))
        self._server_socket.listen(listen_backlog)

    def set_timeout(self, seconds: float) -> None:
        self._server_socket.settimeout(seconds)

    def accept(self):
        client_sock, addr = self._server_socket.accept()
        return TcpConnection(client_sock), addr

    def close(self) -> None:
        self._server_socket.close()
