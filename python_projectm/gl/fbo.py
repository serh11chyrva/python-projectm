"""Framebuffer binding, owned RGBA textures, and CPU readback."""

from contextlib import nullcontext

import numpy as np
from OpenGL import GL

from python_projectm.core.validation import dimensions, integer
from python_projectm.gl.context import ContextGuard
from python_projectm.gl.state import GLStateGuard


class FBO:
    """Temporarily bind a borrowed framebuffer, preserving both bindings and viewport."""

    def __init__(self, fbo_id: int, width: int, height: int):
        self.fbo_id = integer(fbo_id, "fbo_id", minimum=0, maximum=2**32 - 1)
        self.width, self.height = dimensions(width, height)
        self._bindings = []

    def __enter__(self):
        guard = ContextGuard()
        saved = (
            guard,
            int(GL.glGetIntegerv(GL.GL_DRAW_FRAMEBUFFER_BINDING)),
            int(GL.glGetIntegerv(GL.GL_READ_FRAMEBUFFER_BINDING)),
            tuple(GL.glGetIntegerv(GL.GL_VIEWPORT)),
        )
        self._bindings.append(saved)
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, self.fbo_id)
        GL.glViewport(0, 0, self.width, self.height)
        return self

    def __exit__(self, exc_type, exc, tb):
        guard, draw, read, viewport = self._bindings.pop()
        guard.check()
        GL.glBindFramebuffer(GL.GL_DRAW_FRAMEBUFFER, draw)
        GL.glBindFramebuffer(GL.GL_READ_FRAMEBUFFER, read)
        GL.glViewport(*viewport)


class TextureFramebuffer(FBO):
    """Own a single-sample RGBA8 texture and framebuffer in the current context."""

    def __init__(self, width: int, height: int):
        super().__init__(0, width, height)
        self._guard = ContextGuard()
        self._closed = False
        self.texture_id = 0
        with GLStateGuard():
            maximum = int(GL.glGetIntegerv(GL.GL_MAX_TEXTURE_SIZE))
            if max(self.width, self.height) > maximum:
                raise ValueError(f"Framebuffer dimensions exceed GL_MAX_TEXTURE_SIZE ({maximum})")
            try:
                self.texture_id = int(GL.glGenTextures(1))
                self.fbo_id = int(GL.glGenFramebuffers(1))
                GL.glBindBuffer(GL.GL_PIXEL_UNPACK_BUFFER, 0)
                GL.glBindTexture(GL.GL_TEXTURE_2D, self.texture_id)
                GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR)
                GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)
                GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_S, GL.GL_CLAMP_TO_EDGE)
                GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_T, GL.GL_CLAMP_TO_EDGE)
                GL.glTexImage2D(
                    GL.GL_TEXTURE_2D, 0, GL.GL_RGBA8, self.width, self.height,
                    0, GL.GL_RGBA, GL.GL_UNSIGNED_BYTE, None
                )
                GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, self.fbo_id)
                GL.glFramebufferTexture2D(
                    GL.GL_FRAMEBUFFER, GL.GL_COLOR_ATTACHMENT0, GL.GL_TEXTURE_2D, self.texture_id, 0
                )
                GL.glDrawBuffer(GL.GL_COLOR_ATTACHMENT0)
                GL.glReadBuffer(GL.GL_COLOR_ATTACHMENT0)
                status = GL.glCheckFramebufferStatus(GL.GL_FRAMEBUFFER)
                if status != GL.GL_FRAMEBUFFER_COMPLETE:
                    raise RuntimeError(f"Incomplete framebuffer: 0x{int(status):04x}")
            except BaseException:
                self.close()
                raise

    def _check(self):
        if self._closed:
            raise RuntimeError("Framebuffer is closed")
        self._guard.check()

    def __enter__(self):
        self._check()
        return super().__enter__()

    def read(self, *, flip_y: bool = True, out: np.ndarray | None = None,
             preserve_state: bool = True) -> np.ndarray:
        """Return writable contiguous uint8 RGBA pixels; the default origin is top-left."""
        self._check()
        shape = (self.height, self.width, 4)
        if out is None:
            out = np.empty(shape, dtype=np.uint8)
        elif (
            not isinstance(out, np.ndarray) or out.shape != shape or out.dtype != np.uint8
            or not out.flags.c_contiguous or not out.flags.writeable
        ):
            raise ValueError(f"out must be a writable C-contiguous uint8 array of shape {shape}")
        with GLStateGuard() if preserve_state else nullcontext():
            GL.glBindFramebuffer(GL.GL_READ_FRAMEBUFFER, self.fbo_id)
            GL.glReadBuffer(GL.GL_COLOR_ATTACHMENT0)
            GL.glBindBuffer(GL.GL_PIXEL_PACK_BUFFER, 0)
            GL.glPixelStorei(GL.GL_PACK_ALIGNMENT, 1)
            GL.glPixelStorei(GL.GL_PACK_ROW_LENGTH, 0)
            GL.glPixelStorei(GL.GL_PACK_SKIP_PIXELS, 0)
            GL.glPixelStorei(GL.GL_PACK_SKIP_ROWS, 0)
            # Supplying the destination avoids PyOpenGL's implicit buffer allocation.
            GL.glReadPixels(
                0, 0, self.width, self.height, GL.GL_RGBA, GL.GL_UNSIGNED_BYTE, out
            )
        if flip_y:
            out[:] = out[::-1].copy()
        return out

    def close(self) -> None:
        if self._closed:
            return
        self._guard.check()
        if self._bindings:
            raise RuntimeError("Cannot close a framebuffer while it is entered")
        if self.fbo_id:
            GL.glDeleteFramebuffers(1, [self.fbo_id])
        if self.texture_id:
            GL.glDeleteTextures([self.texture_id])
        self.fbo_id = self.texture_id = 0
        self._closed = True

    destroy = close
