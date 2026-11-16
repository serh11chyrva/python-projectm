"""
ProjectM core rendering context.

⚠ Requires an active OpenGL context on the current thread.
"""

from typing import Tuple

from python_projectm.core.errors import ProjectMError, ProjectMNotInitialized
from python_projectm.native import bindings as native


class ProjectMCore:
    def __init__(self):
        self._ctx = native.pypm_create()
        if not self._ctx:
            raise ProjectMError("Failed to create ProjectM context")

        self._alive = True

    def destroy(self) -> None:
        if self._alive:
            native.pypm_destroy(self._ctx)
            self._ctx = None
            self._alive = False

    def __del__(self):
        try:
            self.destroy()
        except Exception:
            pass

    def _check_alive(self):
        if not self._alive or not self._ctx:
            raise ProjectMNotInitialized("ProjectM context is not alive")

    def set_size(self, width: int, height: int) -> None:
        self._check_alive()
        native.pypm_set_window_size(self._ctx, width, height)

    def get_size(self) -> Tuple[int, int]:
        self._check_alive()
        w = native.c_size_t()
        h = native.c_size_t()
        native.pypm_get_window_size(self._ctx, w, h)
        return int(w.value), int(h.value)

    def render(self) -> None:
        self._check_alive()
        native.pypm_render_frame(self._ctx)
