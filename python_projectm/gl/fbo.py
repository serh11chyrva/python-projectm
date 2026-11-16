try:
    from OpenGL.GL import GL_FRAMEBUFFER, glBindFramebuffer, glViewport
except Exception:
    glBindFramebuffer = None


class FBO:
    def __init__(self, fbo_id: int, width: int, height: int):
        self.fbo_id = int(fbo_id)
        self.width = int(width)
        self.height = int(height)

    def __enter__(self):
        if glBindFramebuffer is None:
            raise RuntimeError("OpenGL not available")

        glBindFramebuffer(GL_FRAMEBUFFER, self.fbo_id)  # pyright: ignore[reportPossiblyUnboundVariable]
        glViewport(0, 0, self.width, self.height)
        return self

    def __exit__(self, exc_type, exc, tb):
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
