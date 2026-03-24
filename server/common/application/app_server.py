from common.application.state import ServerState
from server.common.protocol.smile_message import (
    SmileMessage, SmileType
)


class AppServer:
    def __init__(self, state: ServerState | None = None):
        self._state = state or ServerState()

    def handle_message(self, connection, message: SmileMessage):
        if message.type == SmileType.ECHO:
            return self.ok(connection, message.payload)
        if message.type == SmileType.BET:
            return []
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
