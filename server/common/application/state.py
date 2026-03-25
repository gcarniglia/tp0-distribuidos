
from threading import Condition


'''Estado global del negocio de la agencia de lotería'''
class ServerState:
    def __init__(self, total_agencies: int = 5):
        self._total_agencies = total_agencies
        self._ended_agencies = set()
        self._draw_completed = False
        self._draw_condition = Condition()

    def mark_agency_ended(self, agency_id: int) -> bool:
        with self._draw_condition:
            self._ended_agencies.add(agency_id)
            if not self._draw_completed and len(self._ended_agencies) >= self._total_agencies:
                self._draw_completed = True
                self._draw_condition.notify_all()
                return True
            return False

    def wait_for_draw(self):
        with self._draw_condition:
            while not self._draw_completed:
                self._draw_condition.wait()

    def is_draw_completed(self) -> bool:
        with self._draw_condition:
            return self._draw_completed
