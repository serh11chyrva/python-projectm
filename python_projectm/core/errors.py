class ProjectMError(RuntimeError):
    """Base error for ProjectM core API."""


class ProjectMNotInitialized(ProjectMError):
    """Operation attempted on a destroyed or invalid context."""


class ProjectMContextError(ProjectMError):
    """Operation attempted on the wrong thread or without the owning GL context."""
