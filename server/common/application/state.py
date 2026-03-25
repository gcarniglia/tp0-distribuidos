
'''Estado global del servidor. 
Se puede acceder a este estado desde cualquier parte del código'''
class ServerState:
    def __init__(self, total_agencies: int = 5):
        self.shutdown_requested = False
        self.graceful_shutdown_in_progress = False
        self._total_agencies = total_agencies
