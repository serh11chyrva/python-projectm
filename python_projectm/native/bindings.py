"""Lazy ctypes declarations matching pypm_capi.h."""

import ctypes
from ctypes import POINTER, c_char_p, c_double, c_float, c_int, c_size_t, c_uint, c_void_p

from python_projectm.native.errors import NativeError, NativeSymbolError
from python_projectm.native.loader import load_native_library

ContextHandle = c_void_p


class _LazyLibrary:
    def __getattr__(self, name):
        return getattr(load_native_library(), name)


_lib = _LazyLibrary()


def _bind(func_name, *, restype=None, argtypes=()):
    resolved = None

    def function(*args):
        nonlocal resolved
        if resolved is None:
            try:
                candidate = getattr(_lib, func_name)
            except AttributeError as error:
                raise NativeSymbolError(
                    f"Missing native symbol: {func_name}. Rebuild projectM and pypm_capi "
                    "together using the repository's root CMakeLists.txt."
                ) from error
            # None is required for C void functions; ctypes otherwise assumes int.
            candidate.restype = restype
            candidate.argtypes = list(argtypes)
            resolved = candidate
        return resolved(*args)

    function.__name__ = func_name
    return function


pypm_create = _bind("pypm_create", restype=ContextHandle)
pypm_destroy = _bind("pypm_destroy", argtypes=[ContextHandle])
pypm_get_last_error = _bind("pypm_get_last_error", restype=c_char_p)
pypm_clear_error = _bind("pypm_clear_error")

pypm_load_preset_file = _bind(
    "pypm_load_preset_file", restype=c_int, argtypes=[ContextHandle, c_char_p, c_int]
)
pypm_load_preset_data = _bind(
    "pypm_load_preset_data", restype=c_int, argtypes=[ContextHandle, c_char_p, c_int]
)
pypm_reset_textures = _bind("pypm_reset_textures", argtypes=[ContextHandle])
pypm_render_frame = _bind("pypm_render_frame", argtypes=[ContextHandle])
pypm_render_frame_to_fbo = _bind(
    "pypm_render_frame_to_fbo", argtypes=[ContextHandle, c_uint]
)
PYPM_RENDER_BIND_FRAMEBUFFER = 1
PYPM_RENDER_PRESERVE_STATE = 2
pypm_render_frame_ex = _bind(
    "pypm_render_frame_ex", restype=c_int, argtypes=[ContextHandle, c_uint, c_uint]
)

for _name in ("window_size", "mesh_size"):
    globals()[f"pypm_set_{_name}"] = _bind(
        f"pypm_set_{_name}", argtypes=[ContextHandle, c_size_t, c_size_t]
    )
    globals()[f"pypm_get_{_name}"] = _bind(
        f"pypm_get_{_name}", argtypes=[ContextHandle, POINTER(c_size_t), POINTER(c_size_t)]
    )

for _name, _type in (
    ("fps", c_int),
    ("beat_sensitivity", c_float),
    ("preset_duration", c_double),
    ("hard_cut_duration", c_double),
    ("soft_cut_duration", c_double),
    ("hard_cut_sensitivity", c_float),
    ("easter_egg", c_float),
    ("hard_cut_enabled", c_int),
    ("aspect_correction", c_int),
    ("preset_locked", c_int),
):
    globals()[f"pypm_set_{_name}"] = _bind(
        f"pypm_set_{_name}", argtypes=[ContextHandle, _type]
    )
    globals()[f"pypm_get_{_name}"] = _bind(
        f"pypm_get_{_name}", restype=_type, argtypes=[ContextHandle]
    )

pypm_set_texture_search_paths = _bind(
    "pypm_set_texture_search_paths", argtypes=[ContextHandle, POINTER(c_char_p), c_size_t]
)
pypm_pcm_get_max_samples = _bind("pypm_pcm_get_max_samples", restype=c_uint)
for _name, _type in (
    ("float", c_float),
    ("int16", ctypes.c_int16),
    ("uint8", ctypes.c_uint8),
):
    globals()[f"pypm_pcm_add_{_name}"] = _bind(
        f"pypm_pcm_add_{_name}", argtypes=[ContextHandle, POINTER(_type), c_uint, c_uint]
    )

pypm_free_string = _bind("pypm_free_string", argtypes=[c_void_p])
_version_string = _bind("pypm_get_version_string", restype=c_void_p)
_vcs_string = _bind("pypm_get_vcs_version_string", restype=c_void_p)


def check_error() -> None:
    """Raise NativeError when the wrapper's thread-local error string is nonempty."""
    message = pypm_get_last_error()
    if message:
        raise NativeError(message.decode("utf-8", errors="replace"))


def _owned_string(function) -> bytes:
    pypm_clear_error()
    pointer = function()
    check_error()
    if not pointer:
        raise NativeError("projectM could not allocate a version string")
    try:
        return ctypes.string_at(pointer)
    finally:
        pypm_free_string(pointer)


def pypm_get_version_string() -> bytes:
    """Copy the native version to bytes and free its projectM-allocated string."""
    return _owned_string(_version_string)


def pypm_get_vcs_version_string() -> bytes:
    """Copy the native VCS version to bytes and free its projectM-allocated string."""
    return _owned_string(_vcs_string)


__all__ = ["ContextHandle", "check_error"] + [
    name for name in globals() if name.startswith("pypm_")
]
