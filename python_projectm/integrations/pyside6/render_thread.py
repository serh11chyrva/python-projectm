import threading
import time

from PySide6.QtCore import QObject, Signal

from python_projectm.integrations.pyside6.offscreen import GLFWProjectMCPURenderer


class FrameEmitter(QObject):
    frame_ready = Signal(object)


class RenderThread(threading.Thread):
    renderer: GLFWProjectMCPURenderer | None

    def __init__(self, width, height, emitter, fps=60):
        super().__init__(daemon=True)
        self.width = width
        self.height = height
        self.emitter = emitter
        self.delay = 1.0 / fps
        self._running = True
        self.renderer = None

    def run(self):
        self.renderer = GLFWProjectMCPURenderer(self.width, self.height)

        while self._running:
            frame = self.renderer.render_frame()
            self.emitter.frame_ready.emit(frame)
            time.sleep(self.delay)

    def stop(self):
        self._running = False

    def load_preset(self, preset_path):
        if self.renderer is None:
            return
        self.renderer.load_preset(preset_path)
