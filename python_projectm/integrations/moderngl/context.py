"""Adapt ModernGL without importing it or creating another OpenGL context."""

from contextlib import contextmanager, nullcontext

from python_projectm.core.validation import dimensions
from python_projectm.utils.threading import ThreadGuard


class ModernGLContext:
    """Borrow a ModernGL context; keep it current or supply activate().

    activate must return a context manager that makes the native context current,
    for example a GLFWContext.current method. The application owns its lifetime.
    """

    def __init__(self, context, width: int, height: int, *, activate=None):
        if context.version_code < 330:
            raise ValueError("ModernGL integration requires desktop OpenGL 3.3 or newer")
        self.context = context
        self.width, self.height = dimensions(width, height)
        self._activate = activate
        self._thread = ThreadGuard()
        self._activations = []
        self._depth = 0

    def make_current(self) -> None:
        """Enter an activation scope, paired with :meth:`done_current`."""
        self._thread.check()
        manager = self.current()
        manager.__enter__()
        self._activations.append(manager)

    def done_current(self) -> None:
        """Exit the latest activation scope on the creating thread."""
        self._thread.check()
        manager = self._activations.pop()
        manager.__exit__(None, None, None)

    @contextmanager
    def current(self):
        """Activate through the supplied callback, or require an already current context.

        Nested scopes reuse the active native context. The application owns
        both the ModernGL context and the callback's restoration behavior.
        """
        self._thread.check()
        if self._depth:
            self._depth += 1
            try:
                yield self
            finally:
                self._depth -= 1
        else:
            # Detected ModernGL contexts cannot activate a toolkit-owned context.
            with self._activate() if self._activate else nullcontext():
                self._depth = 1
                try:
                    yield self
                finally:
                    self._depth = 0

    def get_size(self) -> tuple[int, int]:
        """Return the adapter's configured physical-pixel output dimensions."""
        self._thread.check()
        return self.width, self.height
