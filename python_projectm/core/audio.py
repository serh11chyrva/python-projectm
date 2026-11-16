"""Validated NumPy PCM input for projectM's mono and stereo audio buffers."""

import ctypes

import numpy as np

from python_projectm.core.errors import ProjectMError
from python_projectm.core.typing import HasContext
from python_projectm.core.validation import integer
from python_projectm.native import bindings as native


def prepare_pcm(samples, channels, dtype) -> tuple[np.ndarray, int]:
    data = np.asarray(samples, dtype=dtype)
    if data.ndim not in (1, 2):
        raise ValueError("PCM must have shape (samples,), (frames, 1), or (frames, 2)")
    if channels is None:
        channels = 1 if data.ndim == 1 else data.shape[1]
    channels = integer(channels, "channels", minimum=1, maximum=2)
    if data.ndim == 2 and data.shape[1] != channels:
        raise ValueError("PCM array shape does not match channels")
    if data.size % channels:
        raise ValueError("Interleaved PCM length must be divisible by channels")
    data = np.ascontiguousarray(data.reshape(-1, channels))
    if data.dtype.kind == "f" and not np.isfinite(data).all():
        raise ValueError("Floating-point PCM samples must be finite")
    return data, channels


class AudioMixin:
    def pcm_max_samples(self: HasContext) -> int:
        return int(self._call(native.pypm_pcm_get_max_samples, with_context=False))

    def _add_pcm(self: HasContext, samples, channels, dtype, ctype, function) -> None:
        self._check_alive()
        data, channels = prepare_pcm(samples, channels, dtype)
        if not len(data):
            return
        maximum = int(self._call(native.pypm_pcm_get_max_samples, with_context=False))
        if maximum <= 0:
            raise ProjectMError("The native PCM sample limit is invalid")
        # Native counts are frames per channel, never the number of scalar values.
        for offset in range(0, len(data), maximum):
            block = data[offset:offset + maximum]
            pointer = block.ctypes.data_as(ctypes.POINTER(ctype))
            self._call(function, pointer, len(block), channels)

    def add_pcm_float(self, samples, channels: int | None = None) -> None:
        """Add floating-point PCM, normally in [-1, 1], with optional channel inference."""
        self._add_pcm(samples, channels, np.float32, ctypes.c_float, native.pypm_pcm_add_float)

    def add_pcm_int16(self, samples, channels: int | None = None) -> None:
        """Add signed 16-bit mono or interleaved stereo PCM."""
        self._add_pcm(samples, channels, np.int16, ctypes.c_int16, native.pypm_pcm_add_int16)

    def add_pcm_uint8(self, samples, channels: int | None = None) -> None:
        """Add unsigned 8-bit PCM, with silence at 128."""
        self._add_pcm(samples, channels, np.uint8, ctypes.c_uint8, native.pypm_pcm_add_uint8)

    def add_pcm(self, samples, channels: int | None = None) -> None:
        """Dispatch floating, int16, or uint8 arrays without guessing integer scaling."""
        data = np.asarray(samples)
        if data.dtype.kind == "f":
            self.add_pcm_float(data, channels)
        elif data.dtype.kind == "i" and data.dtype.itemsize == 2:
            self.add_pcm_int16(data, channels)
        elif data.dtype == np.uint8:
            self.add_pcm_uint8(data, channels)
        else:
            raise TypeError("PCM dtype must be floating point, int16, or uint8")
