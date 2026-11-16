from typing import TypeVar

from python_projectm.core.typing import HasContext
from python_projectm.native import bindings as native

T = TypeVar("T", bound=HasContext)


class ParametersMixin:
    @property
    def beat_sensitivity(self: T) -> float:  # pyright: ignore[reportInvalidTypeVarUse]
        return native.pypm_get_beat_sensitivity(self._ctx)

    @beat_sensitivity.setter
    def beat_sensitivity(self: T, value: float):  # pyright: ignore[reportInvalidTypeVarUse]
        native.pypm_set_beat_sensitivity(self._ctx, float(value))

    @property
    def preset_duration(self: T) -> float:  # pyright: ignore[reportInvalidTypeVarUse]
        return native.pypm_get_preset_duration(self._ctx)

    @preset_duration.setter
    def preset_duration(self: T, value: float):  # pyright: ignore[reportInvalidTypeVarUse]
        native.pypm_set_preset_duration(self._ctx, float(value))

    @property
    def hard_cut_duration(self: T) -> float:  # pyright: ignore[reportInvalidTypeVarUse]
        return native.pypm_get_hard_cut_duration(self._ctx)

    @hard_cut_duration.setter
    def hard_cut_duration(self: T, value: float):  # pyright: ignore[reportInvalidTypeVarUse]
        native.pypm_set_hard_cut_duration(self._ctx, float(value))

    @property
    def soft_cut_duration(self: T) -> float:  # pyright: ignore[reportInvalidTypeVarUse]
        return native.pypm_get_soft_cut_duration(self._ctx)

    @soft_cut_duration.setter
    def soft_cut_duration(self: T, value: float):  # pyright: ignore[reportInvalidTypeVarUse]
        native.pypm_set_soft_cut_duration(self._ctx, float(value))

    @property
    def hard_cut_enabled(self: T) -> bool:  # pyright: ignore[reportInvalidTypeVarUse]
        return bool(native.pypm_get_hard_cut_enabled(self._ctx))

    @hard_cut_enabled.setter
    def hard_cut_enabled(self: T, enabled: bool):  # pyright: ignore[reportInvalidTypeVarUse]
        native.pypm_set_hard_cut_enabled(self._ctx, int(enabled))
