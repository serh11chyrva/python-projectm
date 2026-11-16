from PySide6.QtGui import QOpenGLContext


def is_opengl_context_current() -> bool:
    return QOpenGLContext.currentContext() is not None
