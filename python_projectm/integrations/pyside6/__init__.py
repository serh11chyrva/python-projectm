"""PySide6 GPU widgets, Qt offscreen rendering, and CPU frame display."""

from python_projectm.integrations.pyside6.context import QtGLContext, QtOffscreenContext
from python_projectm.integrations.pyside6.opengl_widget import ProjectMWidget
from python_projectm.integrations.pyside6.render_thread import FrameEmitter, RenderThread
from python_projectm.integrations.pyside6.widget import NumpyViewport
from python_projectm.integrations.pyside6.texture_widget import ThreadedProjectMWidget


def __getattr__(name):
    if name == "GLFWProjectMCPURenderer":
        from python_projectm.integrations.pyside6.offscreen import GLFWProjectMCPURenderer
        return GLFWProjectMCPURenderer
    raise AttributeError(name)


__all__ = [
    "ProjectMWidget", "ThreadedProjectMWidget", "QtGLContext", "QtOffscreenContext", "NumpyViewport",
    "RenderThread", "FrameEmitter", "GLFWProjectMCPURenderer",
]
