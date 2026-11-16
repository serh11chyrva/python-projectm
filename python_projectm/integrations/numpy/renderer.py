"""Render RGBA8 frames into writable NumPy arrays."""

from contextlib import nullcontext

import numpy as np

from python_projectm.core.validation import dimensions
from python_projectm.gl.fbo import TextureFramebuffer
from python_projectm.gl.renderer import Renderer
from python_projectm.gl.state import GLStateGuard


class NumpyRenderer(Renderer):
    """Read projectM frames into CPU memory, borrowing GL or owning a hidden GLFW window."""

    def __init__(self, width: int, height: int, *, context=None, flip_y: bool = True,
                 preserve_state: bool = True):
        width, height = dimensions(width, height)
        self._owns_context = context is None
        self.flip_y = flip_y
        if context is None:
            from python_projectm.integrations.glfw import GLFWContext
            context = GLFWContext(width=width, height=height, visible=False)
        try:
            super().__init__(context, width, height, preserve_state=preserve_state)
            with self.current():
                self._target = TextureFramebuffer(width, height)
        except BaseException:
            if not getattr(self, "_closed", True):
                super().close()
            if self._owns_context:
                context.close()
            raise

    @property
    def framebuffer(self) -> TextureFramebuffer:
        self._check()
        return self._target

    @property
    def texture_id(self) -> int:
        return self.framebuffer.texture_id

    @property
    def window(self):
        """Return the hidden GLFW window when that context provider is in use."""
        return getattr(self.context, "window", None)

    def resize(self, width: int, height: int) -> None:
        width, height = dimensions(width, height)
        if (width, height) == self.size:
            self._check()
            return
        with self.current() as pm:
            replacement = TextureFramebuffer(width, height)
            try:
                pm.set_size(width, height)
            except BaseException:
                replacement.close()
                raise
            previous, self._target = self._target, replacement
            self.width, self.height = width, height
            previous.close()

    def render_frame(self, *, out: np.ndarray | None = None,
                     flip_y: bool | None = None) -> np.ndarray:
        """Return RGBA uint8 (height, width, 4); optionally reuse an output array."""
        with self.current() as pm:
            with GLStateGuard() if self.preserve_state else nullcontext():
                pm.set_size(self.width, self.height)
                pm.render(framebuffer=self._target.fbo_id, preserve_state=False)
                return self._target.read(
                    out=out, flip_y=self.flip_y if flip_y is None else flip_y,
                    preserve_state=False
                )

    render = render_frame

    def close(self) -> None:
        if not self.closed:
            with self.current():
                self._target.close()
            super().close()
        if self._owns_context:
            self.context.close()
