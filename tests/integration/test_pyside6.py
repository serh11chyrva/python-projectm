"""Qt widget framebuffer, queued commands, offscreen and worker lifetimes."""

import queue
import tempfile
import threading
import unittest
from pathlib import Path

import numpy as np

from tests.integration.support import (
    SOLID_PRESET, assert_solid_frame, image_array, require_gl_tests, wait_until,
)

require_gl_tests("PySide6")

from PySide6.QtCore import QCoreApplication, QEvent, QObject, QThread, Slot
from PySide6.QtGui import QOpenGLContext, QSurfaceFormat
from PySide6.QtWidgets import QApplication

from python_projectm.integrations.numpy import NumpyRenderer
from python_projectm.integrations.pyside6 import (
    FrameEmitter, NumpyViewport, ProjectMWidget, QtOffscreenContext, RenderThread,
)
from python_projectm.integrations.pyside6.context import opengl_format


class FrameCollector(QObject):
    def __init__(self):
        super().__init__()
        self.frames = []
        self.threads = []
        self.errors = []
        self.finished = False

    @Slot(object)
    def receive(self, frame):
        self.frames.append(frame)
        self.threads.append(QThread.currentThread())

    @Slot(object)
    def failed(self, error):
        self.errors.append(error)

    @Slot()
    def finish(self):
        self.finished = True


class PySide6Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if QApplication.instance() is None:
            QSurfaceFormat.setDefaultFormat(opengl_format())
        cls.app = QApplication.instance() or QApplication([])
        cls.app.setQuitOnLastWindowClosed(False)

    def setUp(self):
        # Run after each test's widget close/delete callbacks, before another GL context is created.
        self.addCleanup(self.release_qt_events)

    def release_qt_events(self):
        context = QOpenGLContext.currentContext()
        if context is not None:
            context.doneCurrent()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        self.app.processEvents()

    def widget(self):
        widget = ProjectMWidget(fps=30)
        widget.resize(96, 64)
        self.addCleanup(widget.deleteLater)
        self.addCleanup(widget.close)
        return widget

    def test_widget_renders_queued_preset_and_copied_worker_pcm(self):
        widget = self.widget()
        errors = []
        rendered = []
        widget.error.connect(errors.append)
        widget.frame_rendered.connect(lambda: rendered.append(True))
        widget.load_preset_data(SOLID_PRESET, smooth=False)
        widget.show()
        wait_until(self.app, lambda: len(rendered) >= 2 or errors)
        self.assertEqual(errors, [])
        self.assertTrue(widget.isValid())
        samples = np.zeros((512, 2), dtype=np.float32)
        producer = threading.Thread(target=lambda: widget.add_pcm(samples))
        producer.start()
        producer.join(timeout=5)
        self.assertFalse(producer.is_alive())
        samples[:] = np.nan
        previous_count = len(rendered)
        wait_until(self.app, lambda: len(rendered) > previous_count or errors)
        self.assertEqual(errors, [])
        image = widget.grabFramebuffer()
        assert_solid_frame(self, image_array(image), image.width(), image.height())
        with widget.current() as pm:
            self.assertEqual(pm.get_size(), (image.width(), image.height()))
        widget.resize(144, 90)
        widget.fps = 24
        wait_until(self.app, lambda: widget.grabFramebuffer().width() == round(144 * widget.devicePixelRatioF()))
        image = widget.grabFramebuffer()
        assert_solid_frame(self, image_array(image), image.width(), image.height())
        with widget.current() as pm:
            self.assertEqual(pm.fps, 24)
            self.assertEqual(pm.get_size(), (image.width(), image.height()))
            core = pm
        widget.close()
        self.assertTrue(core.closed)
        self.assertIsNone(widget.pm)
        widget.cleanup()
        self.assertEqual(errors, [])

    def test_widget_reports_command_errors_and_continues_rendering(self):
        widget = self.widget()
        errors = []
        rendered = []
        widget.error.connect(errors.append)
        widget.frame_rendered.connect(lambda: rendered.append(True))
        with tempfile.TemporaryDirectory() as directory:
            widget.load_preset_file(Path(directory) / "missing.milk", smooth=False)
            widget.load_preset_data(SOLID_PRESET, smooth=False)
            widget.show()
            wait_until(self.app, lambda: rendered)
        self.assertEqual(len(errors), 1)
        image = widget.grabFramebuffer()
        assert_solid_frame(self, image_array(image), image.width(), image.height())

    def test_qt_offscreen_context_with_numpy(self):
        with QtOffscreenContext() as context:
            with NumpyRenderer(96, 64, context=context) as renderer:
                renderer.load_preset_data(SOLID_PRESET, smooth=False)
                assert_solid_frame(self, renderer.render_frame(), 96, 64)
            with context.current():
                from OpenGL import GL

                self.assertIsNotNone(GL.glGetString(GL.GL_VERSION))

    def test_worker_commands_gui_delivery_resize_and_shutdown(self):
        emitter = FrameEmitter()
        collector = FrameCollector()
        viewport = NumpyViewport(keep_aspect=True)
        self.addCleanup(viewport.deleteLater)
        emitter.frame_ready.connect(collector.receive)
        emitter.frame_ready.connect(viewport.set_frame)
        emitter.error.connect(collector.failed)
        emitter.finished.connect(collector.finish)
        worker = RenderThread(96, 64, emitter, fps=30)
        try:
            worker.load_preset_data(SOLID_PRESET, smooth=False)
            worker.add_pcm(np.zeros((512, 2), dtype=np.float32))
            worker.start()
            wait_until(self.app, lambda: len(collector.frames) >= 2 or collector.errors)
            self.assertEqual(collector.errors, [])
            assert_solid_frame(self, collector.frames[-1], 96, 64)
            worker.resize(80, 48)
            wait_until(self.app, lambda: collector.frames[-1].shape == (48, 80, 4) or collector.errors)
            self.assertEqual(collector.errors, [])
            assert_solid_frame(self, collector.frames[-1], 80, 48)
        finally:
            worker.close()
        wait_until(self.app, lambda: collector.finished)
        self.assertFalse(worker.is_alive())
        self.assertIsNone(worker.renderer)
        self.assertIsNone(worker.error)
        self.assertEqual(collector.errors, [])
        self.assertTrue(all(thread == self.app.thread() for thread in collector.threads))

    def test_worker_queue_is_bounded_and_close_before_start_is_safe(self):
        worker = RenderThread(32, 32, FrameEmitter())
        try:
            for _ in range(128):
                worker.add_pcm(np.zeros(1, dtype=np.float32))
            with self.assertRaises(queue.Full):
                worker.add_pcm(np.zeros(1, dtype=np.float32))
        finally:
            worker.close()
        worker.close()
        with self.assertRaises(RuntimeError):
            worker.resize(64, 64)

    def exercise_example(self, mode):
        from examples._common import DEMO_PRESET
        from examples.pyside6_visualizer import VisualizerWindow, build_parser

        args = build_parser().parse_args(["--mode", mode, "--width", "320", "--height", "180"])
        window = VisualizerWindow(args)
        try:
            window.show()
            wait_until(self.app, lambda: window.frame_count >= 2)
            self.assertEqual(window.error_label.text(), "")
            window.pause_button.click()
            self.assertTrue(window.pause_button.isChecked())
            window.gain_slider.setValue(20)
            window.use_demo_audio()
            self.assertIn("Synthetic stereo", window.audio_label.text())
            with tempfile.TemporaryDirectory() as directory:
                snapshot = Path(directory) / "frame.png"
                window.save_frame(snapshot)
                from PySide6.QtGui import QImage

                image = QImage(str(snapshot))
                self.assertFalse(image.isNull())
                self.assertGreater(float(image_array(image)[:, :, :3].std()), 5.0)
                window.load_preset_path(Path(directory) / "missing.milk", smooth=False)
                wait_until(self.app, lambda: bool(window.error_label.text()))
                window.load_preset_path(DEMO_PRESET, smooth=False)
                count = window.frame_count
                wait_until(self.app, lambda: window.frame_count > count)
                self.assertEqual(window.error_label.text(), "")
        finally:
            window.close()
            window.deleteLater()
        if window.worker is not None:
            self.assertFalse(window.worker.is_alive())
        else:
            self.assertIsNone(window.viewport.pm)

    def test_gpu_example_controls_snapshot_and_error_recovery(self):
        self.exercise_example("gpu")

    def test_worker_example_controls_snapshot_and_error_recovery(self):
        self.exercise_example("worker")
