"""Query the loaded projectM library's version without creating a GL instance."""

from python_projectm.native import bindings as native


def get_version_string() -> str:
    """Return the native projectM version, loading the wrapper on first use.

    This describes projectM rather than the Python distribution. No OpenGL
    context is needed, but matching native runtime libraries must be available.
    """
    return native.pypm_get_version_string().decode("utf-8")


def get_vcs_version_string() -> str:
    """Return the native projectM VCS version string, loading the wrapper if needed."""
    return native.pypm_get_vcs_version_string().decode("utf-8")
