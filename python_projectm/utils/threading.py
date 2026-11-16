import threading


class ThreadGuard:
    def __init__(self):
        self._thread_id = threading.get_ident()

    def check(self):
        if threading.get_ident() != self._thread_id:
            raise RuntimeError("Object used from wrong thread")
