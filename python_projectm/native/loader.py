"""Load the wrapper and retain Windows DLL search directories for its lifetime."""

import ctypes
import os
import sys
from functools import lru_cache
from pathlib import Path

from python_projectm.native.errors import NativeError, NativeLibraryNotFound

LIB_NAME = {
    "win32": "pypm_capi.dll",
    "darwin": "libpypm_capi.dylib",
}.get(sys.platform, "libpypm_capi.so")

_dll_directories: dict[str, object] = {}


def _native_bin_dir() -> Path:
    return Path(__file__).resolve().parent / "bin"


def _load_dependencies_windows(bin_dir: Path) -> None:
    if sys.platform == "win32" and str(bin_dir) not in _dll_directories:
        # Closing or discarding this handle removes the DLL search directory.
        _dll_directories[str(bin_dir)] = os.add_dll_directory(str(bin_dir))


@lru_cache(maxsize=1)
def load_native_library() -> ctypes.CDLL:
    """Load the packaged library, or the file selected by PYTHON_PROJECTM_LIBRARY."""
    override = os.environ.get("PYTHON_PROJECTM_LIBRARY")
    library = Path(override).expanduser().resolve() if override else _native_bin_dir() / LIB_NAME
    if not library.is_file():
        raise NativeLibraryNotFound(
            f"Native library not found: {library}. Build the native wrapper as described in README.md."
        )
    try:
        _load_dependencies_windows(library.parent)
        return ctypes.CDLL(str(library))
    except OSError as error:
        raise NativeError(
            f"Cannot load {library}: {error}. Check the projectM runtime libraries, "
            "the C++ runtime, and that Python and the native libraries use the same architecture."
        ) from error


@lru_cache(maxsize=1)
def load_glew_library() -> ctypes.CDLL:
    """Load GLEW for callers using the legacy helper; the wrapper initializes it."""
    if sys.platform != "win32":
        raise NativeError("The standalone GLEW loader is Windows-only")
    override = os.environ.get("PYTHON_PROJECTM_LIBRARY")
    bin_dir = Path(override).expanduser().resolve().parent if override else _native_bin_dir()
    library = bin_dir / "glew32.dll"
    if not library.is_file():
        raise NativeLibraryNotFound(f"GLEW library not found: {library}")
    _load_dependencies_windows(bin_dir)
    return ctypes.WinDLL(str(library))


__all__ = ["load_native_library", "load_glew_library"]
