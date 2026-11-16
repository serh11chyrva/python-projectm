"""Render projectM directly into a GLFW window's drawable."""

import glfw

from python_projectm.gl.renderer import Renderer
from python_projectm.integrations.glfw.context import GLFWContext, _main_thread


class GLFWRenderer(Renderer):
    """Render to a borrowed GLFW window or create an owned OpenGL 3.3 window.

    Args:
        window: Existing GLFW window, or ``None`` to create one.
        width: Initial logical window width when creating a window.
        height: Initial logical window height when creating a window.
        title: Title used for an owned window.
        visible: Whether an owned window is visible.
        preserve_state: Preserve the GL state used by rendering.

    Construct, poll, render, and close on the main thread. Only owned windows
    are destroyed; the application remains responsible for ``glfw.terminate``.
    Output dimensions follow the window's physical framebuffer size.
    """

    def __init__(self, window=None, *, width: int = 1280, height: int = 720,
                 title: str = "projectM", visible: bool = True,
                 preserve_state: bool = True):
        context = GLFWContext(window, width=width, height=height, title=title, visible=visible)
        try:
            framebuffer_width, framebuffer_height = context.get_size()
            super().__init__(
                context, max(1, framebuffer_width), max(1, framebuffer_height),
                preserve_state=preserve_state
            )
        except BaseException:
            context.close()
            raise
        self.window = context.window

    @property
    def should_close(self) -> bool:
        """Whether GLFW has requested closing this window."""
        self._check()
        _main_thread()
        return bool(glfw.window_should_close(self.window))

    def poll_events(self) -> None:
        """Poll global GLFW events on the main thread."""
        self._check()
        _main_thread()
        glfw.poll_events()

    def render(self, *, swap_buffers: bool = True) -> bool:
        """Render using the current framebuffer size; skip minimized windows.

        Args:
            swap_buffers: Present the completed frame after rendering.

        Returns:
            True if rendered, or False if either framebuffer dimension is zero.
        """
        self._check()
        width, height = self.context.get_size()
        if width <= 0 or height <= 0:
            return False
        with self.current() as pm:
            pm.set_size(width, height)
            self.width, self.height = width, height
            pm.render(framebuffer=0, preserve_state=self.preserve_state)
            if swap_buffers:
                glfw.swap_buffers(self.window)
        return True

    def close(self) -> None:
        """Close projectM before destroying an owned window; retain borrowed windows."""
        super().close()
        self.context.close()
