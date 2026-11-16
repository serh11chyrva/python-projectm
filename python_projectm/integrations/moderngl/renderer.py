"""Render into ModernGL textures without a CPU copy or a separate GL context."""

from python_projectm.core.validation import dimensions
from python_projectm.gl.renderer import Renderer
from python_projectm.gl.state import GLStateGuard
from python_projectm.integrations.moderngl.context import ModernGLContext


class ModernGLRenderer(Renderer):
    def __init__(self, context, width: int, height: int, *, activate=None,
                 preserve_state: bool = True):
        adapter = ModernGLContext(context, width, height, activate=activate)
        self.gl = context
        self.texture = self.framebuffer = None
        try:
            super().__init__(adapter, width, height, preserve_state=preserve_state)
            with self.current():
                self.texture, self.framebuffer = self._allocate(width, height)
        except BaseException:
            if not getattr(self, "_closed", True):
                super().close()
            raise

    def _allocate(self, width, height):
        with GLStateGuard():
            texture = self.gl.texture((width, height), components=4, dtype="f1")
            try:
                framebuffer = self.gl.framebuffer(color_attachments=[texture])
            except BaseException:
                texture.release()
                raise
            return texture, framebuffer

    def render(self, framebuffer=None):
        """Render to the owned texture or a borrowed ModernGL framebuffer."""
        self._check()
        target = self.framebuffer if framebuffer is None else framebuffer
        if target.ctx is not self.gl:
            raise ValueError("The framebuffer must belong to this ModernGL context")
        width, height = dimensions(*target.size)
        with self.current() as pm:
            pm.set_size(width, height)
            pm.render(framebuffer=target.glo, preserve_state=self.preserve_state)
        return self.texture if framebuffer is None else target

    def render_frame(self, framebuffer=None):
        return self.render(framebuffer)

    def resize(self, width: int, height: int) -> None:
        width, height = dimensions(width, height)
        self._check()
        if (width, height) == self.size:
            return
        with self.current() as pm:
            texture, framebuffer = self._allocate(width, height)
            try:
                pm.set_size(width, height)
            except BaseException:
                framebuffer.release()
                texture.release()
                raise
            previous_texture, previous_framebuffer = self.texture, self.framebuffer
            self.texture, self.framebuffer = texture, framebuffer
            self.width, self.height = width, height
            self.context.width, self.context.height = width, height
            previous_framebuffer.release()
            previous_texture.release()

    def close(self) -> None:
        if self.closed:
            return
        with self.current():
            self.framebuffer.release()
            self.texture.release()
        super().close()
