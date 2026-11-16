import ctypes
from typing import TypeVar

import numpy as np

from python_projectm.core.typing import HasContext
from python_projectm.native import bindings as native

T = TypeVar("T", bound=HasContext)


class AudioMixin:
    def pcm_max_samples(self: T) -> int:  # pyright: ignore[reportInvalidTypeVarUse]
        return native.pypm_pcm_get_max_samples()

    def add_pcm_float(self: T, samples: np.ndarray, channels: int):  # pyright: ignore[reportInvalidTypeVarUse]
        samples = np.asarray(samples, dtype=np.float32)
        if not samples.flags["C_CONTIGUOUS"]:
            samples = np.ascontiguousarray(samples)

        ptr = samples.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
        frames = samples.shape[0]

        native.pypm_pcm_add_float(
            self._ctx,
            ptr,
            frames,
            channels,
        )
