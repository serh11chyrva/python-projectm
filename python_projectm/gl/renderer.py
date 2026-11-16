"""Common context adapter protocol and managed projectM renderer."""

import threading
from contextlib import contextmanager
from typing import Protocol

from python_projectm.core.validation import dimensions
from python_projectm.gl.context import use_context


class GLContext(Protocol):
    """Minimal adapter for a toolkit-owned OpenGL context."""

    def make_current(self) -> None:
        """Make the context current on the calling thread."""

    def done_current(self) -> None:
        """Release the context, preferably restoring the preceding one."""

    def get_size(self) -> tuple[int, int]:
        """Return the drawable size in physical pixels."""


class Renderer:
    """Manage projectM while borrowing a context supplied by the application."""

    def __init__(self, context: GLContext, width: int | None = None,
                 height: int | None = None, *, preserve_state: bool = True):
        from python_projectm.core import ProjectM

        self.context = context
        self.preserve_state = preserve_state
        self._thread_id = threading.get_ident()
        self._closed = True
        if width is None and height is None:
            width, height = context.get_size()
        self.width, self.height = dimensions(width, height)
        with use_context(context):
            self.pm = ProjectM()
            try:
                self.pm.set_size(self.width, self.height)
            except BaseException:
                self.pm.close()
                raise
        self._closed = False

    @property
    def closed(self) -> bool:
        return self._closed

    @property
    def size(self) -> tuple[int, int]:
        return self.width, self.height

    def _check(self) -> None:
        if self._closed:
            raise RuntimeError("Renderer is closed")
        if threading.get_ident() != self._thread_id:
            raise RuntimeError("Renderer must be used on its creating thread")

    @contextmanager
    def current(self):
        """Make the borrowed context current and expose the complete ProjectM API."""
        self._check()
        with use_context(self.context):
            self.pm._check_alive()
            yield self.pm

    def resize(self, width: int, height: int) -> None:
        width, height = dimensions(width, height)
        with self.current() as pm:
            pm.set_size(width, height)
        self.width, self.height = width, height

    def render(self, *, framebuffer: int | None = None) -> None:
        with self.current() as pm:
            pm.render(framebuffer=framebuffer, preserve_state=self.preserve_state)

    def render_frame(self):
        return self.render()

    def load_preset_file(self, path, *, smooth: bool = True) -> None:
        with self.current() as pm:
            pm.load_preset_file(path, smooth=smooth)

    def load_preset(self, path, *, smooth: bool = True) -> None:
        self.load_preset_file(path, smooth=smooth)

    def load_preset_data(self, data: str, *, smooth: bool = True) -> None:
        with self.current() as pm:
            pm.load_preset_data(data, smooth=smooth)

    def add_pcm(self, samples, channels: int | None = None) -> None:
        with self.current() as pm:
            pm.add_pcm(samples, channels)

    def add_pcm_float(self, samples, channels: int | None = None) -> None:
        with self.current() as pm:
            pm.add_pcm_float(samples, channels)

    def add_pcm_int16(self, samples, channels: int | None = None) -> None:
        with self.current() as pm:
            pm.add_pcm_int16(samples, channels)

    def add_pcm_uint8(self, samples, channels: int | None = None) -> None:
        with self.current() as pm:
            pm.add_pcm_uint8(samples, channels)

    def close(self) -> None:
        if self._closed:
            return
        self._check()
        with use_context(self.context):
            self.pm.close()
        self._closed = True

    def destroy(self) -> None:
        self.close()

    def __enter__(self):
        self._check()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
