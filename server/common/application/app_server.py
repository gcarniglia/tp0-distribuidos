from common.protocol.smile_message import (
    SmileMessage, SmileType
)


class AppServer:

    def handle_message(self, connection, message: SmileMessage):
        if message.type == SmileType.ECHO:
            return self.ok(connection, message.payload), True, None
        if message.type == SmileType.BET:
            return [], True, None
        if message.type == SmileType.BATCH:
            return [], True, None
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
