from typing import TypeVar

from python_projectm.core.errors import ProjectMError
from python_projectm.core.typing import HasContext
from python_projectm.native import bindings as native

T = TypeVar("T", bound=HasContext)


class PresetsMixin:
    def load_preset_file(self: T, path: str, *, smooth: bool = True) -> None:  # pyright: ignore[reportInvalidTypeVarUse]
        ok = native.pypm_load_preset_file(
            self._ctx,
            path.encode("utf-8"),
            int(smooth),
        )
        if not ok:
            raise ProjectMError(f"Failed to load preset file: {path}")

    def load_preset_data(self: T, data: str, *, smooth: bool = True) -> None:  # pyright: ignore[reportInvalidTypeVarUse]
        ok = native.pypm_load_preset_data(
            self._ctx,
            data.encode("utf-8"),
            int(smooth),
        )
        if not ok:
            raise ProjectMError("Failed to load preset data")

    def reset_textures(self: T) -> None:  # pyright: ignore[reportInvalidTypeVarUse]
        native.pypm_reset_textures(self._ctx)
