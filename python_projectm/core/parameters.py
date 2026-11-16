"""Parameters exposed by the projectM 4 C API."""

import ctypes
import os

from python_projectm.core.validation import dimensions, encoded_text, integer, nonnegative
from python_projectm.gl.state import GLStateGuard, prepare_render_state
from python_projectm.native import bindings as native


def _parameter(name, convert, validate=None):
    def get(self):
        return convert(self._call(getattr(native, f"pypm_get_{name}")))

    def set(self, value):
        value = validate(value) if validate else convert(value)
        self._call(getattr(native, f"pypm_set_{name}"), value)

    return property(get, set, doc=f"The projectM {name.replace('_', ' ')} setting.")


class ParametersMixin:
    """Read and update projectM settings with the owning OpenGL context current.

    Numeric sensitivity and duration settings must be finite and nonnegative.
    Durations are measured in seconds; ``fps`` must be a positive integer.
    Setting the frame rate informs projectM and does not pace a render loop.
    """

    beat_sensitivity = _parameter("beat_sensitivity", float, nonnegative)
    preset_duration = _parameter("preset_duration", float, nonnegative)
    hard_cut_duration = _parameter("hard_cut_duration", float, nonnegative)
    soft_cut_duration = _parameter("soft_cut_duration", float, nonnegative)
    hard_cut_sensitivity = _parameter("hard_cut_sensitivity", float, nonnegative)
    easter_egg = _parameter("easter_egg", float, nonnegative)
    hard_cut_enabled = _parameter("hard_cut_enabled", bool)
    aspect_correction = _parameter("aspect_correction", bool)
    preset_locked = _parameter("preset_locked", bool)
    fps = _parameter("fps", int, lambda value: integer(value, "fps"))

    def set_mesh_size(self, width: int, height: int) -> None:
        """Set the preset evaluation mesh to positive integer dimensions."""
        width, height = dimensions(width, height)
        self._call(native.pypm_set_mesh_size, width, height)

    def get_mesh_size(self) -> tuple[int, int]:
        """Return the preset evaluation mesh ``(width, height)``."""
        width, height = ctypes.c_size_t(), ctypes.c_size_t()
        self._call(native.pypm_get_mesh_size, ctypes.byref(width), ctypes.byref(height))
        return width.value, height.value

    @property
    def mesh_size(self) -> tuple[int, int]:
        """Preset evaluation mesh dimensions as a writable ``(width, height)`` pair."""
        return self.get_mesh_size()

    @mesh_size.setter
    def mesh_size(self, size) -> None:
        self.set_mesh_size(*size)

    def set_texture_search_paths(self, paths) -> None:
        """Replace texture directories and immediately rebuild the texture cache.

        ``paths`` may be a string, a path-like object, or an iterable of either.
        An empty iterable clears the configured search paths. The owning GL
        context must be current because rebuilding changes GPU resources.
        """
        self._check_alive()
        if isinstance(paths, (str, os.PathLike)):
            paths = [paths]
        encoded = [encoded_text(os.fspath(path), "texture path") for path in paths]
        pointers = (ctypes.c_char_p * len(encoded))(*encoded)
        with GLStateGuard(check_resources=True):
            prepare_render_state()
            self._call(native.pypm_set_texture_search_paths, pointers, len(encoded))
