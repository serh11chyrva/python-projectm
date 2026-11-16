"""Exercise the rebuilt C API, GLFW windows, FBOs, and NumPy readback."""

import tempfile
import threading
import unittest
from pathlib import Path

import numpy as np

from tests.integration.support import SOLID_PRESET, assert_solid_frame, require_gl_tests

require_gl_tests("glfw")

import glfw
from OpenGL import GL

from python_projectm import ProjectM
from python_projectm.core.errors import ProjectMContextError, ProjectMError, ProjectMNotInitialized
from python_projectm.core.version import get_version_string
from python_projectm.gl.fbo import TextureFramebuffer
from python_projectm.gl.state import GLStateGuard
from python_projectm.integrations.glfw import GLFWContext, GLFWRenderer
from python_projectm.integrations.numpy import NumpyRenderer


class GLContextTests(unittest.TestCase):
    def setUp(self):
        self.addCleanup(glfw.terminate)
        self.context = GLFWContext(width=96, height=64, visible=False)
        self.addCleanup(self.context.close)

    def test_version_parameters_and_all_pcm_formats(self):
        self.assertEqual(get_version_string(), "4.1.6")
        with self.context.current(), ProjectM() as pm:
            pm.set_size(96, 64)
            self.assertEqual(pm.get_size(), (96, 64))
            pm.mesh_size = (32, 24)
            self.assertEqual(pm.mesh_size, (32, 24))
            for name, value in (("fps", 30), ("beat_sensitivity", 1.5),
                                ("preset_duration", 20.0), ("soft_cut_duration", 2.0),
                                ("hard_cut_duration", 10.0), ("hard_cut_sensitivity", 1.2),
                                ("easter_egg", 0.0)):
                with self.subTest(parameter=name):
                    setattr(pm, name, value)
                    self.assertAlmostEqual(getattr(pm, name), value, places=5)
            for name in ("hard_cut_enabled", "aspect_correction", "preset_locked"):
                for value in (True, False):
                    setattr(pm, name, value)
                    self.assertEqual(getattr(pm, name), value)
            count = pm.pcm_max_samples() + 17
            pm.add_pcm_float(np.zeros((count, 2), dtype=np.float32))
            pm.add_pcm_int16(np.zeros(count, dtype=np.int16))
            pm.add_pcm_uint8(np.full((count, 2), 128, dtype=np.uint8))
            pm.set_texture_search_paths([])
            pm.reset_textures()

    def test_explicit_target_and_caller_gl_state_are_preserved(self):
        with self.context.current(), ProjectM() as pm, GLStateGuard():
            target = TextureFramebuffer(96, 64)
            sentinel = TextureFramebuffer(96, 64)
            try:
                with sentinel:
                    GL.glClearColor(0.9, 0.1, 0.3, 1.0)
                    GL.glClear(GL.GL_COLOR_BUFFER_BIT)
                pm.set_size(96, 64)
                pm.load_preset_data(SOLID_PRESET, smooth=False)
                GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, sentinel.fbo_id)
                GL.glViewport(2, 3, 7, 9)
                GL.glScissor(1, 1, 2, 2)
                GL.glEnable(GL.GL_SCISSOR_TEST)
                GL.glColorMask(False, True, False, True)
                GL.glPixelStorei(GL.GL_PACK_ALIGNMENT, 8)
                pm.render(framebuffer=target.fbo_id)
                self.assertEqual(int(GL.glGetIntegerv(GL.GL_DRAW_FRAMEBUFFER_BINDING)), sentinel.fbo_id)
                self.assertEqual(int(GL.glGetIntegerv(GL.GL_READ_FRAMEBUFFER_BINDING)), sentinel.fbo_id)
                self.assertEqual(tuple(GL.glGetIntegerv(GL.GL_VIEWPORT)), (2, 3, 7, 9))
                self.assertTrue(GL.glIsEnabled(GL.GL_SCISSOR_TEST))
                self.assertEqual(tuple(GL.glGetBooleanv(GL.GL_COLOR_WRITEMASK)), (False, True, False, True))
                self.assertEqual(int(GL.glGetIntegerv(GL.GL_PACK_ALIGNMENT)), 8)
                assert_solid_frame(self, target.read(), 96, 64)
                np.testing.assert_allclose(sentinel.read()[32, 48, :3], [230, 26, 76], atol=1)
            finally:
                sentinel.close()
                target.close()

    def test_preset_file_failure_recovers_and_close_is_idempotent(self):
        with self.context.current(), ProjectM() as pm:
            with tempfile.TemporaryDirectory() as directory:
                preset = Path(directory) / "sample.milk"
                with self.assertRaises(ProjectMError):
                    pm.load_preset_file(preset, smooth=False)
                preset.write_text(SOLID_PRESET, encoding="utf-8")
                pm.load_preset_file(preset, smooth=False)
            pm.set_size(0, 0)
            pm.render()
            pm.close()
            pm.close()
            self.assertTrue(pm.closed)
            with self.assertRaises(ProjectMNotInitialized):
                pm.get_size()

    def test_core_rejects_another_thread_and_another_context(self):
        with self.context.current(), ProjectM() as pm:
            errors = []

            def access_from_worker():
                try:
                    pm.get_size()
                except Exception as error:
                    errors.append(error)

            worker = threading.Thread(target=access_from_worker)
            worker.start()
            worker.join(timeout=5)
            self.assertFalse(worker.is_alive())
            self.assertEqual(len(errors), 1)
            self.assertIsInstance(errors[0], ProjectMContextError)
            other = GLFWContext(width=32, height=32, visible=False)
            try:
                with other.current(), self.assertRaises(ProjectMContextError):
                    pm.get_size()
            finally:
                other.close()
            self.assertFalse(pm.closed)

    def test_glfw_renders_into_a_borrowed_window(self):
        renderer = GLFWRenderer(self.context.window)
        try:
            renderer.load_preset_data(SOLID_PRESET, smooth=False)
            self.assertTrue(renderer.render(swap_buffers=False))
            with renderer.current():
                width, height = renderer.size
                frame = np.empty((height, width, 4), dtype=np.uint8)
                GL.glReadBuffer(GL.GL_BACK)
                GL.glReadPixels(0, 0, width, height, GL.GL_RGBA, GL.GL_UNSIGNED_BYTE, frame)
                assert_solid_frame(self, frame, width, height)
        finally:
            renderer.close()
        with self.context.current():
            self.assertIsNotNone(GL.glGetString(GL.GL_VERSION))
        renderer.close()

    def test_numpy_reuses_output_resizes_and_borrows_context(self):
        renderer = NumpyRenderer(96, 64, context=self.context)
        try:
            renderer.load_preset_data(SOLID_PRESET, smooth=False)
            out = np.empty((64, 96, 4), dtype=np.uint8)
            self.assertIs(renderer.render_frame(out=out), out)
            self.assertTrue(out.flags.writeable)
            assert_solid_frame(self, out, 96, 64)
            renderer.resize(80, 48)
            assert_solid_frame(self, renderer.render_frame(), 80, 48)
            with self.assertRaises(ValueError):
                renderer.render_frame(out=out)
        finally:
            renderer.close()
        with self.context.current():
            self.assertIsNotNone(GL.glGetString(GL.GL_VERSION))

    def test_numpy_rejects_invalid_output_buffers(self):
        with NumpyRenderer(96, 64, context=self.context) as renderer:
            renderer.load_preset_data(SOLID_PRESET, smooth=False)
            readonly = np.zeros((64, 96, 4), dtype=np.uint8)
            readonly.flags.writeable = False
            for out in (readonly, np.zeros((64, 96, 4), dtype=np.float32),
                        np.zeros((64, 192, 4), dtype=np.uint8)[:, ::2],
                        np.zeros((64, 96, 3), dtype=np.uint8)):
                with self.subTest(shape=out.shape, dtype=out.dtype), self.assertRaises(ValueError):
                    renderer.render_frame(out=out)

    def test_numpy_vertical_flip_and_default_context(self):
        gradient = SOLID_PRESET.replace("float3(0.2, 0.4, 0.8)", "float3(uv.y, 0.4, 0.8)")
        with NumpyRenderer(96, 64) as renderer:
            renderer.load_preset_data(gradient, smooth=False)
            bottom_left = renderer.render_frame(flip_y=False)
            top_left = renderer.render_frame(flip_y=True)
            np.testing.assert_array_equal(top_left, bottom_left[::-1])
            self.assertGreater(abs(int(top_left[8, 48, 0]) - int(top_left[-9, 48, 0])), 100)
        self.assertTrue(renderer.closed)
