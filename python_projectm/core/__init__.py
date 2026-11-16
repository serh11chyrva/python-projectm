"""Core projectM API for applications with a current desktop OpenGL context."""

from python_projectm.core.audio import AudioMixin
from python_projectm.core.context import ProjectMCore
from python_projectm.core.errors import ProjectMContextError, ProjectMError, ProjectMNotInitialized
from python_projectm.core.parameters import ParametersMixin
from python_projectm.core.presets import PresetsMixin


class ProjectM(ProjectMCore, PresetsMixin, ParametersMixin, AudioMixin):
    """Render presets and submit PCM in the current desktop OpenGL context.

    Combines instance lifetime, preset loading, parameters, and audio input.
    Construction requires desktop OpenGL 3.3 or newer. Use every method on the
    creating thread with the original context current, including ``close()``.
    A ``with`` statement closes the instance without closing the GL context.

    Raises:
        ProjectMContextError: No suitable OpenGL context is current.
        ProjectMError: The native projectM instance could not be created.
    """

    pass


__all__ = [
    "ProjectM",
    "ProjectMCore",
    "ProjectMError",
    "ProjectMNotInitialized",
    "ProjectMContextError",
]
