import ctypes
from ctypes import (
    POINTER,
    c_char_p,
    c_double,
    c_float,
    c_int,
    c_size_t,
    c_uint,
    c_void_p,
)

from python_projectm.native.errors import NativeSymbolError
from python_projectm.native.loader import load_native_library

_lib = load_native_library()


ContextHandle = c_void_p


def _bind(func_name, *, restype=None, argtypes=None):
    try:
        fn = getattr(_lib, func_name)
    except AttributeError as e:
        raise NativeSymbolError(f"Missing symbol: {func_name}") from e

    if restype is not None:
        fn.restype = restype
    if argtypes is not None:
        fn.argtypes = argtypes

    return fn


pypm_create = _bind(
    "pypm_create",
    restype=ContextHandle,
)

pypm_destroy = _bind(
    "pypm_destroy",
    argtypes=[ContextHandle],
)


pypm_load_preset_file = _bind(
    "pypm_load_preset_file",
    restype=c_int,
    argtypes=[ContextHandle, c_char_p, c_int],
)

pypm_load_preset_data = _bind(
    "pypm_load_preset_data",
    restype=c_int,
    argtypes=[ContextHandle, c_char_p, c_int],
)

pypm_reset_textures = _bind(
    "pypm_reset_textures",
    argtypes=[ContextHandle],
)


pypm_render_frame = _bind(
    "pypm_render_frame",
    argtypes=[ContextHandle],
)

pypm_set_window_size = _bind(
    "pypm_set_window_size",
    argtypes=[ContextHandle, c_size_t, c_size_t],
)

pypm_get_window_size = _bind(
    "pypm_get_window_size",
    argtypes=[ContextHandle, POINTER(c_size_t), POINTER(c_size_t)],
)


pypm_set_fps = _bind(
    "pypm_set_fps",
    argtypes=[ContextHandle, c_int],
)

pypm_get_fps = _bind(
    "pypm_get_fps",
    restype=c_int,
    argtypes=[ContextHandle],
)


pypm_set_beat_sensitivity = _bind(
    "pypm_set_beat_sensitivity",
    argtypes=[ContextHandle, c_float],
)

pypm_get_beat_sensitivity = _bind(
    "pypm_get_beat_sensitivity",
    restype=c_float,
    argtypes=[ContextHandle],
)

pypm_set_preset_duration = _bind(
    "pypm_set_preset_duration",
    argtypes=[ContextHandle, c_double],
)

pypm_get_preset_duration = _bind(
    "pypm_get_preset_duration",
    restype=c_double,
    argtypes=[ContextHandle],
)

pypm_set_hard_cut_duration = _bind(
    "pypm_set_hard_cut_duration",
    argtypes=[ContextHandle, c_double],
)

pypm_get_hard_cut_duration = _bind(
    "pypm_get_hard_cut_duration",
    restype=c_double,
    argtypes=[ContextHandle],
)

pypm_set_soft_cut_duration = _bind(
    "pypm_set_soft_cut_duration",
    argtypes=[ContextHandle, c_double],
)

pypm_get_soft_cut_duration = _bind(
    "pypm_get_soft_cut_duration",
    restype=c_double,
    argtypes=[ContextHandle],
)

pypm_set_hard_cut_enabled = _bind(
    "pypm_set_hard_cut_enabled",
    argtypes=[ContextHandle, c_int],
)

pypm_get_hard_cut_enabled = _bind(
    "pypm_get_hard_cut_enabled",
    restype=c_int,
    argtypes=[ContextHandle],
)


pypm_set_mesh_size = _bind(
    "pypm_set_mesh_size",
    argtypes=[ContextHandle, c_size_t, c_size_t],
)

pypm_get_mesh_size = _bind(
    "pypm_get_mesh_size",
    argtypes=[ContextHandle, POINTER(c_size_t), POINTER(c_size_t)],
)

pypm_set_aspect_correction = _bind(
    "pypm_set_aspect_correction",
    argtypes=[ContextHandle, c_int],
)

pypm_get_aspect_correction = _bind(
    "pypm_get_aspect_correction",
    restype=c_int,
    argtypes=[ContextHandle],
)


pypm_pcm_get_max_samples = _bind(
    "pypm_pcm_get_max_samples",
    restype=c_uint,
)

pypm_pcm_add_float = _bind(
    "pypm_pcm_add_float",
    argtypes=[
        ContextHandle,
        POINTER(c_float),
        c_uint,
        c_uint,
    ],
)

pypm_pcm_add_int16 = _bind(
    "pypm_pcm_add_int16",
    argtypes=[
        ContextHandle,
        POINTER(ctypes.c_int16),
        c_uint,
        c_uint,
    ],
)

pypm_pcm_add_uint8 = _bind(
    "pypm_pcm_add_uint8",
    argtypes=[
        ContextHandle,
        POINTER(ctypes.c_uint8),
        c_uint,
        c_uint,
    ],
)


pypm_get_version_string = _bind(
    "pypm_get_version_string",
    restype=c_char_p,
)

pypm_get_vcs_version_string = _bind(
    "pypm_get_vcs_version_string",
    restype=c_char_p,
)


__all__ = [
    # types
    "ContextHandle",
    # lifecycle
    "pypm_create",
    "pypm_destroy",
    # presets
    "pypm_load_preset_file",
    "pypm_load_preset_data",
    "pypm_reset_textures",
    # rendering
    "pypm_render_frame",
    "pypm_set_window_size",
    "pypm_get_window_size",
    # timing
    "pypm_set_fps",
    "pypm_get_fps",
    # beat / transitions
    "pypm_set_beat_sensitivity",
    "pypm_get_beat_sensitivity",
    "pypm_set_preset_duration",
    "pypm_get_preset_duration",
    "pypm_set_hard_cut_duration",
    "pypm_get_hard_cut_duration",
    "pypm_set_soft_cut_duration",
    "pypm_get_soft_cut_duration",
    "pypm_set_hard_cut_enabled",
    "pypm_get_hard_cut_enabled",
    # mesh / aspect
    "pypm_set_mesh_size",
    "pypm_get_mesh_size",
    "pypm_set_aspect_correction",
    "pypm_get_aspect_correction",
    # audio
    "pypm_pcm_get_max_samples",
    "pypm_pcm_add_float",
    "pypm_pcm_add_int16",
    "pypm_pcm_add_uint8",
    # version
    "pypm_get_version_string",
    "pypm_get_vcs_version_string",
]
