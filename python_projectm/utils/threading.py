"""Thread ownership checks for OpenGL context adapters."""

import threading


class ThreadGuard:
    """Record the creating thread for resources that cannot cross threads."""

    def __init__(self):
        self._thread_id = threading.get_ident()

    def check(self):
        """Raise RuntimeError when called from a different thread."""
        if threading.get_ident() != self._thread_id:
            raise RuntimeError("Object used from wrong thread")
