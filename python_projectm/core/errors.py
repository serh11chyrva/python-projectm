class ProjectMError(RuntimeError):
    """Base error for ProjectM core API."""


class ProjectMNotInitialized(ProjectMError):
    """Operation attempted on a destroyed or invalid context."""
