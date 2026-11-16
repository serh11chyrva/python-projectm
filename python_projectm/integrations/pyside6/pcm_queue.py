"""Reusable PCM storage whose ownership ends after the render thread consumes it."""

import threading

import numpy as np


class PCMBufferPool:
    """Keep at most ``capacity`` free arrays; queued arrays are never reused."""

    def __init__(self, capacity: int = 128):
        self._capacity = capacity
        self._free = {}
        self._count = 0
        self._lock = threading.Lock()

    def copy(self, samples) -> np.ndarray:
        """Copy producer data once, converting supported PCM to its native dtype."""
        source = np.asarray(samples)
        dtype = source.dtype
        if dtype.kind == "f":
            dtype = np.dtype(np.float32)
        elif dtype.kind == "i" and dtype.itemsize == 2:
            dtype = np.dtype(np.int16)
        key = (source.shape, dtype.str)
        with self._lock:
            buffers = self._free.get(key)
            if buffers:
                result = buffers.pop()
                self._count -= 1
                if not buffers:
                    del self._free[key]
            else:
                result = None
        if result is None:
            result = np.empty(source.shape, dtype=dtype)
        np.copyto(result, source, casting="unsafe")
        return result

    def release(self, buffer: np.ndarray) -> None:
        """Return storage only after the native PCM call has finished."""
        with self._lock:
            if self._count < self._capacity:
                key = (buffer.shape, buffer.dtype.str)
                self._free.setdefault(key, []).append(buffer)
                self._count += 1

    def clear(self) -> None:
        """Drop free storage after shutdown; in-flight producer copies stay owned."""
        with self._lock:
            self._free.clear()
            self._count = 0
