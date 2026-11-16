"""Validated NumPy PCM input for projectM's mono and stereo audio buffers."""

import ctypes

import numpy as np

from python_projectm.core.errors import ProjectMError
from python_projectm.core.typing import HasContext
from python_projectm.core.validation import integer
from python_projectm.native import bindings as native


def prepare_pcm(samples, channels, dtype) -> tuple[np.ndarray, int]:
    """Return contiguous ``(frames, channels)`` PCM and the validated channel count.

    Convert to ``dtype`` and infer mono from a flat array, or the channel count
    from a two-dimensional array. Only one or two channels are supported.
    Floating-point samples must be finite; input values are not normalized.
    """
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
    """Submit mono or interleaved stereo PCM to a live projectM instance.

    Inputs have shape ``(frames,)``, ``(frames, 1)``, or ``(frames, 2)``. A flat
    array defaults to mono; pass ``channels=2`` for flat interleaved stereo.
    Noncontiguous input is copied and large blocks are split automatically.
    These methods analyze audio without capturing, playing, or resampling it.
    Call them on the owning rendering thread with its context current.
    """

    def pcm_max_samples(self: HasContext) -> int:
        """Return and cache the native maximum frames per channel in one call."""
        self._check_alive()
        maximum = getattr(self, "_pcm_limit", None)
        if maximum is None:
            maximum = int(self._call(native.pypm_pcm_get_max_samples, with_context=False))
            if maximum <= 0:
                raise ProjectMError("The native PCM sample limit is invalid")
            self._pcm_limit = maximum
        return maximum

    def _add_pcm(self: HasContext, samples, channels, dtype, ctype, function) -> None:
        self._check_alive()
        data, channels = prepare_pcm(samples, channels, dtype)
        if not len(data):
            return
        maximum = self.pcm_max_samples()
        # Native counts are frames per channel, never the number of scalar values.
        for offset in range(0, len(data), maximum):
            block = data[offset:offset + maximum]
            pointer = block.ctypes.data_as(ctypes.POINTER(ctype))
            self._call(function, pointer, len(block), channels)

    def add_pcm_float(self, samples, channels: int | None = None) -> None:
        """Add PCM converted to float32, normally in the range [-1, 1].

        Args:
            samples: Finite mono or interleaved stereo samples.
            channels: One or two, or ``None`` to infer from the array shape.

        Values are not clipped or rescaled.
        """
        self._add_pcm(samples, channels, np.float32, ctypes.c_float, native.pypm_pcm_add_float)

    def add_pcm_int16(self, samples, channels: int | None = None) -> None:
        """Add mono or interleaved stereo PCM converted to signed int16.

        ``channels`` is one or two, or inferred when omitted. Values are cast
        without normalization; provide samples in the signed 16-bit PCM range.
        """
        self._add_pcm(samples, channels, np.int16, ctypes.c_int16, native.pypm_pcm_add_int16)

    def add_pcm_uint8(self, samples, channels: int | None = None) -> None:
        """Add mono or interleaved stereo PCM converted to uint8, with silence at 128.

        ``channels`` is one or two, or inferred when omitted. Values are cast
        without normalization; provide samples in the unsigned 8-bit PCM range.
        """
        self._add_pcm(samples, channels, np.uint8, ctypes.c_uint8, native.pypm_pcm_add_uint8)

    def add_pcm(self, samples, channels: int | None = None) -> None:
        """Dispatch floating-point, int16, or uint8 PCM by the input array's dtype.

        Args:
            samples: Mono or interleaved stereo PCM with a supported dtype.
            channels: One or two, or ``None`` to infer from the array shape.

        Raises:
            TypeError: The inferred array dtype is unsupported, for example int64.
            ValueError: The shape, channel count, or floating-point values are invalid.
        """
        data = np.asarray(samples)
        if data.dtype.kind == "f":
            self.add_pcm_float(data, channels)
        elif data.dtype.kind == "i" and data.dtype.itemsize == 2:
            self.add_pcm_int16(data, channels)
        elif data.dtype == np.uint8:
            self.add_pcm_uint8(data, channels)
        else:
            raise TypeError("PCM dtype must be floating point, int16, or uint8")
