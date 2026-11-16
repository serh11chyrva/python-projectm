"""
Native library loader for python-projectm.

Loads pypm_capi shared library from the package's native/bin directory.

This module is INTERNAL. Do not use it directly.
"""

import ctypes
import os
import sys
from typing import Final

try:
    # Python 3.9+
    from importlib.resources import files
except ImportError:  # pragma: no cover
    from importlib_resources import files  # type: ignore


if sys.platform == "win32":
    LIB_NAME: Final[str] = "pypm_capi.dll"
elif sys.platform == "darwin":
    LIB_NAME = "libpypm_capi.dylib"
else:
    LIB_NAME = "libpypm_capi.so"


def _native_bin_dir():
    return files("python_projectm.native").joinpath("bin")


def _load_dependencies_windows(bin_dir) -> None:
    """
    On Windows, ensure dependent DLLs are discoverable.

    ctypes.CDLL accepts full paths, but dependent DLLs
    must still be discoverable by the loader.
    """
    if sys.platform != "win32":
        return

    try:
        os.add_dll_directory(str(bin_dir))
    except (AttributeError, FileNotFoundError):
        # AttributeError: Python < 3.8 (not supported anyway)
        # FileNotFoundError: directory missing (handled later)
        pass


def load_native_library() -> ctypes.CDLL:
    bin_dir = _native_bin_dir()
    lib = bin_dir.joinpath(LIB_NAME)

    if not lib.exists():
        raise RuntimeError(
            "Native library not found.\n"
            f"Expected: {lib}\n\n"
            "This usually means:\n"
            "- the package was installed without native binaries\n"
            "- or the wheel is broken\n"
            "- or you are running from a source checkout without building natives\n\n"
            "If building manually, run CMake and ensure binaries are copied into:\n"
            "  python_projectm/native/bin/"
        )

    # Windows: ensure dependent DLLs are discoverable
    _load_dependencies_windows(bin_dir)

    try:
        return ctypes.CDLL(str(lib))
    except OSError as exc:
        raise RuntimeError(
            "Failed to load native library.\n"
            f"Path: {lib}\n"
            f"Error: {exc}\n\n"
            "Possible causes:\n"
            "- missing dependent libraries (projectM, OpenGL, glew32, etc.)\n"
            "- incompatible architecture (32/64 bit mismatch)\n"
            "- incompatible C runtime\n"
        ) from exc


def load_glew_library() -> ctypes.CDLL:
    if sys.platform != "win32":
        raise RuntimeError("GLEW loader is Windows-only")

    bin_dir = _native_bin_dir()
    glew = bin_dir.joinpath("glew32.dll")

    if not glew.exists():
        raise RuntimeError(f"glew32.dll not found.\nExpected: {glew}")

    _load_dependencies_windows(bin_dir)

    return ctypes.WinDLL(str(glew))


__all__ = ["load_native_library", "load_glew_library"]
