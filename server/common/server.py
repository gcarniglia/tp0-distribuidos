import logging
import signal
import threading

from common.application.app_server import AppServer
from common.protocol.smile_protocol import SmileProtocol
from common.protocol.smile_errors import SmileError, PayloadTooLargeError
from .protocol.smile_message import SmileMessage, SmileType
from common.transport.tcp_server import TcpServer
from common.application.state import ServerState


class Server:
    def __init__(self, port, listen_backlog, total_agencies=5):
        self._tcp_server = TcpServer(port, listen_backlog)
        self._codec = SmileProtocol()
        self._app = AppServer(ServerState(total_agencies=total_agencies))
        self._shutdown_requested = threading.Event()
        self._connections_lock = threading.Lock()
        self._active_connections = set()
        self._worker_threads = set()
        signal.signal(signal.SIGTERM, self._on_sigterm)
    
    ''' Loop principal del servidor, que se encarga de aceptar conexiones '''
    def run(self):
        try:
            while not self._shutdown_requested.is_set():
                connection = self.__accept_new_connection()
                if connection is None:
                    continue
                self.__spawn_connection_worker(connection)
        finally:
            self.__shutdown()

    ''' Handler de la señal SIGTERM para realizar un apagado ordenado del servidor '''
    def _on_sigterm(self, signum, frame):
        _ = signum
        _ = frame
        self._shutdown_requested.set()
        self._tcp_server.close()

    ''' Crea un nuevo hilo para manejar la conexión del cliente 
    y lo agrega a la lista de conexiones activas '''
    def __spawn_connection_worker(self, connection):
        with self._connections_lock:
            self._active_connections.add(connection)

        worker = threading.Thread(target=self.__handle_client_connection, args=(connection,))
        worker.start()
        with self._connections_lock:
            self._worker_threads.add(worker)
    
    ''' Atiende la conexión del cliente, recibiendo mensajes y enviando respuestas 
    hasta que el cliente se desconecte o se reciba un mensaje de shutdown '''
    def __handle_client_connection(self, connection):
        try:
            while True:
                try:
                    # Decodificación de Mensaje recibido
                    message = self._codec.decode_from(connection)
                except EOFError:
                    # Cliente cerró la conexión de forma inesperada, 
                    # se termina el loop de atención de esta conexión
                    break
                except PayloadTooLargeError as exc:
                    # escenario cuando se envía un payload mayor a 8KB
                    # Se descarta el mensaje completo y se envía un mensaje de error al cliente, 
                    # pero se mantiene la conexión abierta
                    self.__send_message(connection, SmileMessage(SmileType.ERROR, str(exc).encode("utf-8")))
                    _ = connection.read_exactly(exc.payload_len)
                    continue
                except SmileError as exc:
                    # Escenario de error en protocolo, como por ejemplo un mensaje mal formado.
                    # Se envía un mensaje de error al cliente y se cierra la conexión
                    self.__send_message(connection, SmileMessage(SmileType.ERROR, str(exc).encode("utf-8")))
                    break

                logging.info(
                    "action: receive_message | result: success | ip: %s | msg: %s",
                    connection.peer_ip(),
                    self.__safe_payload_preview(message.payload),
                )
                
                # Escenario de cierre de conexión ordenado por parte del cliente, 
                # se termina el loop de atención de esta conexión
                if message.type == SmileType.SHUTDOWN:
                    logging.info("action: shutdown_received | result: success | ip: %s", connection.peer_ip())
                    break
                
                self.__process_message(connection, message)

        # Gracefull shutdown de la conexión con el cliente
        finally:
            with self._connections_lock:
                self._active_connections.discard(connection)
            connection.close()

    ''' Procesa un mensaje recibido del cliente, ejecutando la lógica de negocio
    y enviando una respuesta al cliente destinatario'''
    def __process_message(self, connection, message):
        responses = self._app.handle_message(connection, message)
        for target_connection, response_message in responses:
            self.__send_message(target_connection, response_message)

    '''Acepta una nueva conexión TCP entrante'''
    def __accept_new_connection(self):
        logging.info('action: accept_connections | result: in_progress')
        try:
            conn, addr = self._tcp_server.accept()
            logging.info(f'action: accept_connections | result: success | ip: {addr[0]}')
            return conn
        except OSError as exc:
            if not self._shutdown_requested.is_set():
                logging.error(f'action: accept_connections | result: fail | error: {exc}')
            return None

    '''Envía un mensaje a través de una conexión TCP, manejando errores de envío'''
    def __send_message(self, connection, message):
        try:
            frame = self._codec.encode(message)
            connection.send_all(frame)
        except OSError as exc:
            logging.error(f'action: send_message | result: fail | error: {exc}')

    '''Realiza un apagado ordenado del servidor completo, 
    cerrando conexiones activas y esperando a que los hilos de trabajo terminen'''
    def __shutdown(self):
        self._shutdown_requested.set()

        with self._connections_lock:
            active_connections = list(self._active_connections)
            worker_threads = list(self._worker_threads)

        for connection in active_connections:
            self.__send_message(connection, SmileMessage(SmileType.SHUTDOWN, b""))
            connection.close()

        self._tcp_server.close()

        for worker in worker_threads:
            worker.join(timeout=2.0)

    
    '''Representacion segura del payload para logs'''
    @staticmethod
    def __safe_payload_preview(payload: bytes):
        try:
            return payload.decode('utf-8')
        except UnicodeDecodeError:
            return str(payload)
