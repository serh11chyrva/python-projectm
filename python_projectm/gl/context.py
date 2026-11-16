"""Context identity and thread ownership without depending on a window toolkit."""

import threading
from contextlib import contextmanager

from OpenGL import GL, platform

from python_projectm.core.errors import ProjectMContextError


def current_context_id() -> int:
    """Return the current native OpenGL context identifier, or zero if absent."""
    return int(platform.PLATFORM.GetCurrentContext() or 0)


class ContextGuard:
    """Require the creating thread and exactly the creating native GL context."""

    def __init__(self):
        self.thread_id = threading.get_ident()
        self.context_id = current_context_id()
        if not self.context_id:
            raise ProjectMContextError("An OpenGL context must be current on this thread")

    def check(self) -> None:
        """Raise ProjectMContextError if the creating thread or context differs."""
        if threading.get_ident() != self.thread_id:
            raise ProjectMContextError("OpenGL resources must be used on their creating thread")
        if current_context_id() != self.context_id:
            raise ProjectMContextError("The resource's original OpenGL context must be current")


def require_desktop_gl() -> None:
    """Raise ProjectMContextError unless desktop OpenGL 3.3+ is current."""
    version = GL.glGetString(GL.GL_VERSION)
    if not version or version.startswith(b"OpenGL ES"):
        raise ProjectMContextError("projectM requires a desktop OpenGL 3.3 or newer context")
    major = int(GL.glGetIntegerv(GL.GL_MAJOR_VERSION))
    minor = int(GL.glGetIntegerv(GL.GL_MINOR_VERSION))
    if (major, minor) < (3, 3):
        raise ProjectMContextError(f"OpenGL 3.3 or newer is required; received {major}.{minor}")


@contextmanager
def use_context(context):
    """Use an adapter's restoring context manager or its legacy make/done pair."""
    current = getattr(context, "current", None)
    if current is not None:
        with current():
            yield
    else:
        context.make_current()
        try:
            yield
        finally:
            context.done_current()
