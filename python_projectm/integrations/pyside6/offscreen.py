import ctypes

import glfw
import numpy as np
from OpenGL import GL

from python_projectm.core import ProjectM
from python_projectm.native.loader import load_glew_library


class GLFWProjectMCPURenderer:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height

        if not glfw.init():
            raise RuntimeError("GLFW init failed")

        glfw.window_hint(glfw.VISIBLE, glfw.FALSE)
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 4)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 6)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_COMPAT_PROFILE)

        self.window = glfw.create_window(
            width, height, "projectM-offscreen", None, None
        )
        if not self.window:
            raise RuntimeError("Failed to create GLFW window")

        glfw.make_context_current(self.window)

        # ---- GLEW ----
        glew = load_glew_library()
        glew.glewExperimental = ctypes.c_ubyte(1)
        glew.glewInit.restype = ctypes.c_uint
        if glew.glewInit() != 0:
            raise RuntimeError("glewInit failed")

        # ---- projectM ----
        self.pm = ProjectM()
        self.pm.set_size(width, height)

    def render_frame(self) -> np.ndarray:
        glfw.make_context_current(self.window)

        GL.glViewport(0, 0, self.width, self.height)
        GL.glClearColor(0.0, 0.0, 0.0, 1.0)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)

        self.pm.render()

        data = GL.glReadPixels(
            0,
            0,
            self.width,
            self.height,
            GL.GL_RGBA,
            GL.GL_UNSIGNED_BYTE,
        )

        frame = np.frombuffer(data, dtype=np.uint8)
        frame = frame.reshape((self.height, self.width, 4))
        frame = np.flipud(frame)  # OpenGL → Qt

        return frame.copy()

    def load_preset(self, path: str):
        glfw.make_context_current(self.window)
        self.pm.load_preset_file(path, smooth=True)
