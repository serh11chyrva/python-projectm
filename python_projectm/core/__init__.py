from python_projectm.core.audio import AudioMixin
from python_projectm.core.context import ProjectMCore
from python_projectm.core.errors import ProjectMError
from python_projectm.core.parameters import ParametersMixin
from python_projectm.core.presets import PresetsMixin


class ProjectM(ProjectMCore, PresetsMixin, ParametersMixin, AudioMixin):
    """Full ProjectM core API."""

    pass


__all__ = [
    "ProjectM",
    "ProjectMCore",
    "ProjectMError",
]
