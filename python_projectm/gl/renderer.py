from typing import Protocol, Tuple


class GLContext(Protocol):
    """
    Abstract OpenGL context interface.

    Implementations:
    - QOpenGLWidget
    - GLFW window
    - EGL / headless context
    """

    def make_current(self) -> None:
        """Make this OpenGL context current on the calling thread."""

    def done_current(self) -> None:
        """Release this OpenGL context."""

    def get_size(self) -> Tuple[int, int]:  # pyright: ignore[reportReturnType]
        """Return (width, height) of the render target."""
