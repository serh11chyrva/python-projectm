"""Compatibility import for the original GLFW-backed CPU renderer."""

from python_projectm.integrations.numpy import NumpyRenderer


class GLFWProjectMCPURenderer(NumpyRenderer):
    """Legacy name for NumpyRenderer with its default hidden GLFW context."""
