from typing import Tuple

from PySide6.QtGui import QOpenGLContext

from python_projectm.gl.renderer import GLContext


class QtGLContext(GLContext):
    def __init__(self, ctx: QOpenGLContext):
        self._ctx = ctx

    def make_current(self) -> None:
        self._ctx.makeCurrent(self._ctx.surface())

    def done_current(self) -> None:
        self._ctx.doneCurrent()

    def get_size(self) -> Tuple[int, int]:
        surface = self._ctx.surface()
        size = surface.size()
        return size.width(), size.height()
