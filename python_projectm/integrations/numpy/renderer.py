"""Render RGBA8 frames into writable NumPy arrays."""

from contextlib import nullcontext

import numpy as np

from python_projectm.core.validation import dimensions
from python_projectm.gl.fbo import TextureFramebuffer
from python_projectm.gl.renderer import Renderer
from python_projectm.gl.state import GLStateGuard


class NumpyRenderer(Renderer):
    """Read projectM frames into CPU memory through desktop OpenGL.

    Args:
        width: Positive frame width in physical pixels.
        height: Positive frame height in physical pixels.
        context: Borrowed GL adapter, or ``None`` to own a hidden GLFW window.
            The default requires the ``glfw`` extra and main-thread use.
        flip_y: Return frames with a top-left origin by default.
        preserve_state: Preserve the GL state used by rendering and readback.

    Returned frames are writable, C-contiguous RGBA uint8 arrays. This renderer
    performs GPU-to-CPU readback and still needs an OpenGL implementation.
    """

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
        """Owned output framebuffer; resize and close invalidate this resource."""
        self._check()
        return self._target

    @property
    def texture_id(self) -> int:
        """OpenGL ID of the current owned RGBA8 texture."""
        return self.framebuffer.texture_id

    @property
    def window(self):
        """Return the hidden GLFW window when that context provider is in use."""
        return getattr(self.context, "window", None)

    def resize(self, width: int, height: int) -> None:
        """Replace the output framebuffer with positive physical-pixel dimensions."""
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
        """Render and read an RGBA uint8 array of shape ``(height, width, 4)``.

        Args:
            out: Optional writable C-contiguous uint8 destination of the exact
                output shape. It is returned directly instead of allocating.
            flip_y: Override the renderer's row orientation for this frame.
                ``None`` uses the constructor setting.

        Returns:
            A writable, C-contiguous frame, or the supplied ``out`` array.
        """
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
        """Release output resources and projectM, then close an owned GLFW context.

        Borrowed adapters remain alive. The application controls global GLFW
        termination, including when this renderer created a hidden window.
        """
        if not self.closed:
            with self.current():
                self._target.close()
            super().close()
        if self._owns_context:
            self.context.close()
