"""Toolkit-independent projectM instance bound to one thread and GL context."""

import ctypes
import warnings
from contextlib import nullcontext

from OpenGL import GL

from python_projectm.core.errors import ProjectMError, ProjectMNotInitialized
from python_projectm.core.validation import dimensions, integer
from python_projectm.gl.context import ContextGuard, require_desktop_gl
from python_projectm.gl.state import GLStateGuard, prepare_render_state
from python_projectm.native import bindings as native
from python_projectm.native.errors import NativeError


class ProjectMCore:
    """Create and use this object with the same desktop OpenGL context current."""

    def __init__(self):
        self._alive = False
        self._ctx = None
        self._guard = ContextGuard()
        require_desktop_gl()
        with GLStateGuard():
            prepare_render_state()
            try:
                # Detect an outdated wrapper before it can allocate a native instance.
                native.pypm_clear_error()
                self._ctx = native.pypm_create()
                self._alive = bool(self._ctx)
                native.check_error()
            except NativeError as error:
                raise ProjectMError(str(error)) from error
        if not self._alive:
            raise ProjectMError("Failed to create projectM")

    @property
    def closed(self) -> bool:
        return not self._alive

    def _check_alive(self) -> None:
        if not self._alive or not self._ctx:
            raise ProjectMNotInitialized("ProjectM context is closed")
        self._guard.check()

    def _call(self, function, *args, with_context: bool = True):
        self._check_alive()
        try:
            result = function(self._ctx, *args) if with_context else function(*args)
            native.check_error()
            return result
        except NativeError as error:
            raise ProjectMError(str(error)) from error

    def destroy(self) -> None:
        """Release native resources before the owning GL context is destroyed."""
        if not self._alive:
            return
        self._check_alive()
        with GLStateGuard(check_resources=True):
            self._call(native.pypm_destroy)
            self._ctx = None
            self._alive = False

    close = destroy

    def __enter__(self):
        self._check_alive()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.destroy()

    def __del__(self):
        if getattr(self, "_alive", False):
            try:
                self._guard.check()
                self.destroy()
            except Exception:
                warnings.warn(
                    "ProjectM was not closed before its context or thread became unavailable; "
                    "use close() or a with statement.",
                    ResourceWarning,
                    stacklevel=2,
                )

    def set_size(self, width: int, height: int) -> None:
        width, height = dimensions(width, height, allow_zero=True)
        self._call(native.pypm_set_window_size, width, height)

    def get_size(self) -> tuple[int, int]:
        width, height = ctypes.c_size_t(), ctypes.c_size_t()
        self._call(native.pypm_get_window_size, ctypes.byref(width), ctypes.byref(height))
        return width.value, height.value

    def render(self, *, framebuffer: int | None = None, preserve_state: bool = True) -> None:
        """Render into the current draw framebuffer or an explicit framebuffer ID."""
        self._check_alive()
        if framebuffer is not None:
            framebuffer = integer(framebuffer, "framebuffer", minimum=0, maximum=2**32 - 1)
        width, height = self.get_size()
        if width == 0 or height == 0:
            return
        with GLStateGuard() if preserve_state else nullcontext():
            prepare_render_state()
            GL.glViewport(0, 0, width, height)
            if framebuffer is None:
                self._call(native.pypm_render_frame)
            else:
                self._call(native.pypm_render_frame_to_fbo, framebuffer)
