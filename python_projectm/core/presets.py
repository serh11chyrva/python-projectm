"""Preset loading with native failure reporting."""

import os

from python_projectm.core.errors import ProjectMError
from python_projectm.core.validation import encoded_text
from python_projectm.gl.state import GLStateGuard, prepare_render_state
from python_projectm.native import bindings as native


class PresetsMixin:
    def load_preset_file(self, path: str | os.PathLike[str], *, smooth: bool = True) -> None:
        """Load a Milkdrop file or an upstream URL such as idle://."""
        self._check_alive()
        encoded = encoded_text(os.fspath(path), "preset path")
        with GLStateGuard(check_resources=True):
            prepare_render_state()
            ok = self._call(native.pypm_load_preset_file, encoded, int(smooth))
        if not ok:
            raise ProjectMError(f"Failed to load preset file: {path}")

    def load_preset_data(self, data: str, *, smooth: bool = True) -> None:
        self._check_alive()
        encoded = encoded_text(data, "preset data")
        with GLStateGuard(check_resources=True):
            prepare_render_state()
            ok = self._call(native.pypm_load_preset_data, encoded, int(smooth))
        if not ok:
            raise ProjectMError("Failed to load preset data")

    def reset_textures(self) -> None:
        self._check_alive()
        with GLStateGuard(check_resources=True):
            prepare_render_state()
            self._call(native.pypm_reset_textures)
