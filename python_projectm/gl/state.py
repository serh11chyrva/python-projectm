try:
    from OpenGL.GL import GL_VIEWPORT, glGetIntegerv, glViewport
except Exception:
    glGetIntegerv = None


class ViewportGuard:
    def __enter__(self):
        if glGetIntegerv is None:
            raise RuntimeError("OpenGL not available")

        self._old = glGetIntegerv(GL_VIEWPORT)  # pyright: ignore[reportPossiblyUnboundVariable]
        return self

    def __exit__(self, exc_type, exc, tb):
        x, y, w, h = self._old
        glViewport(x, y, w, h)
