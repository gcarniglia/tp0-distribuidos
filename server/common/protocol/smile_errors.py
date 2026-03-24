class SmileError(Exception):
    pass


class PayloadTooLargeError(SmileError):
    def __init__(self, payload_len: int):
        super().__init__(f"payload length exceeds max allowed: {payload_len}")
        self.payload_len = payload_len
