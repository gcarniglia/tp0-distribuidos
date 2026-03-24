import logging
import signal
import socket
import threading

from common.application.app_server import AppServer
from common.protocol.codec import Codec, PayloadTooLargeError, ProtocolError
from common.protocol.messages import Message, MSG_ERROR, MSG_SHUTDOWN
from common.transport.tcp_server import TcpServer


class Server:
    def __init__(self, port, listen_backlog):
        self._tcp_server = TcpServer(port, listen_backlog)
        self._tcp_server.set_timeout(1.0)
        self._codec = Codec()
        self._app = AppServer()
        self._shutdown_requested = threading.Event()
        self._connections_lock = threading.Lock()
        self._active_connections = set()
        self._worker_threads = set()
        signal.signal(signal.SIGTERM, self._on_sigterm)

    def run(self):
        try:
            while not self._shutdown_requested.is_set():
                connection = self.__accept_new_connection()
                if connection is None:
                    continue
                self.__spawn_connection_worker(connection)
        finally:
            self.__shutdown()

    def _on_sigterm(self, signum, frame):
        _ = signum
        _ = frame
        self._shutdown_requested.set()

    def __spawn_connection_worker(self, connection):
        with self._connections_lock:
            self._active_connections.add(connection)

        worker = threading.Thread(target=self.__handle_client_connection, args=(connection,))
        worker.start()
        with self._connections_lock:
            self._worker_threads.add(worker)

    def __handle_client_connection(self, connection):
        try:
            while not self._shutdown_requested.is_set():
                try:
                    message = self._codec.decode_from(connection)
                except socket.timeout:
                    continue
                except EOFError:
                    break
                except PayloadTooLargeError as exc:
                    self.__send_message(connection, Message(MSG_ERROR, str(exc).encode("utf-8")))
                    _ = connection.read_exactly(exc.payload_len)
                    continue
                except ProtocolError as exc:
                    self.__send_message(connection, Message(MSG_ERROR, str(exc).encode("utf-8")))
                    break

                logging.info(
                    "action: receive_message | result: success | ip: %s | msg: %s",
                    connection.peer_ip(),
                    self.__safe_payload_preview(message.payload),
                )

                responses = self._app.handle_message(connection, message)
                for target_connection, response_message in responses:
                    self.__send_message(target_connection, response_message)
        finally:
            with self._connections_lock:
                self._active_connections.discard(connection)
            connection.close()

    def __accept_new_connection(self):
        logging.info('action: accept_connections | result: in_progress')
        try:
            conn, addr = self._tcp_server.accept()
            conn.settimeout(1.0)
            logging.info(f'action: accept_connections | result: success | ip: {addr[0]}')
            return conn
        except socket.timeout:
            return None
        except OSError as exc:
            if not self._shutdown_requested.is_set():
                logging.error(f'action: accept_connections | result: fail | error: {exc}')
            return None

    def __send_message(self, connection, message):
        try:
            frame = self._codec.encode(message)
            connection.send_all(frame)
        except OSError as exc:
            logging.error(f'action: send_message | result: fail | error: {exc}')

    def __shutdown(self):
        self._shutdown_requested.set()

        with self._connections_lock:
            active_connections = list(self._active_connections)
            worker_threads = list(self._worker_threads)

        for connection in active_connections:
            self.__send_message(connection, Message(MSG_SHUTDOWN, b""))
            connection.close()

        self._tcp_server.close()

        for worker in worker_threads:
            worker.join(timeout=2.0)

    @staticmethod
    def __safe_payload_preview(payload: bytes):
        try:
            return payload.decode('utf-8')
        except UnicodeDecodeError:
            return str(payload)
