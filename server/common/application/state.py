import os
import threading


class ServerState:
    def __init__(self):
        self.shutdown_requested = False
        self.graceful_shutdown_in_progress = False
        self.expected_agencies = int(os.getenv("EXPECTED_AGENCY_COUNT", "5"))
        self.finished_agencies = set()
        self.draw_ready = False
        self.pending_winner_requests = []
        self.persistence_lock = threading.Lock()
        self.state_lock = threading.Lock()
