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
    """Manage projectM while borrowing a context supplied by the application.

    Args:
        context: Adapter implementing :class:`GLContext`. A restoring
            ``current()`` context manager is used when available.
        width: Positive output width in physical pixels. If both dimensions
            are omitted, use ``context.get_size()``.
        height: Positive output height in physical pixels.
        preserve_state: Preserve the GL state used by each render call.

    Use the renderer on its creating thread. Methods activate the context for
    their duration; a renderer's ``with`` statement only manages its lifetime.
    ``close()`` destroys projectM and leaves the borrowed context alive.
    """

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
        """Whether the managed projectM instance has been closed."""
        return self._closed

    @property
    def size(self) -> tuple[int, int]:
        """Current output ``(width, height)`` in physical pixels."""
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
        """Set positive output dimensions, activating the borrowed context."""
        width, height = dimensions(width, height)
        with self.current() as pm:
            pm.set_size(width, height)
        self.width, self.height = width, height

    def render(self, *, framebuffer: int | None = None) -> None:
        """Render to the current draw framebuffer or an explicit OpenGL FBO ID."""
        with self.current() as pm:
            pm.render(framebuffer=framebuffer, preserve_state=self.preserve_state)

    def render_frame(self):
        """Call :meth:`render`; subclasses may return a texture or CPU frame."""
        return self.render()

    def load_preset_file(self, path, *, smooth: bool = True) -> None:
        """Load a preset path or projectM URL with the context active."""
        with self.current() as pm:
            pm.load_preset_file(path, smooth=smooth)

    def load_preset(self, path, *, smooth: bool = True) -> None:
        """Call :meth:`load_preset_file` using the compatibility method name."""
        self.load_preset_file(path, smooth=smooth)

    def load_preset_data(self, data: str, *, smooth: bool = True) -> None:
        """Load Milkdrop source text, optionally requesting a smooth transition."""
        with self.current() as pm:
            pm.load_preset_data(data, smooth=smooth)

    def add_pcm(self, samples, channels: int | None = None) -> None:
        """Submit floating-point, int16, or uint8 PCM with the context active.

        A flat array defaults to mono. Use ``channels=2`` for flat interleaved
        stereo, or pass a ``(frames, 2)`` array to infer stereo automatically.
        """
        with self.current() as pm:
            pm.add_pcm(samples, channels)

    def add_pcm_float(self, samples, channels: int | None = None) -> None:
        """Submit PCM converted to float32; the usual input range is [-1, 1]."""
        with self.current() as pm:
            pm.add_pcm_float(samples, channels)

    def add_pcm_int16(self, samples, channels: int | None = None) -> None:
        """Submit mono or interleaved stereo PCM converted to signed int16."""
        with self.current() as pm:
            pm.add_pcm_int16(samples, channels)

    def add_pcm_uint8(self, samples, channels: int | None = None) -> None:
        """Submit PCM converted to uint8, where 128 represents silence."""
        with self.current() as pm:
            pm.add_pcm_uint8(samples, channels)

    def close(self) -> None:
        """Close projectM with its context active, retaining the borrowed context.

        Call on the creating thread before destroying the native context.
        Repeated calls do nothing.
        """
        if self._closed:
            return
        self._check()
        with use_context(self.context):
            self.pm.close()
        self._closed = True

    def destroy(self) -> None:
        """Call :meth:`close` using the compatibility method name."""
        self.close()

    def __enter__(self):
        self._check()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
