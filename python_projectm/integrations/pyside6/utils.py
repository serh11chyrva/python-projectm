"""Small Qt context inspection helpers."""

from PySide6.QtGui import QOpenGLContext


def is_opengl_context_current() -> bool:
    """Return whether Qt reports a current OpenGL context on the calling thread."""
    return QOpenGLContext.currentContext() is not None
