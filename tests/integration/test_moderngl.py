"""Real ModernGL texture output and ownership of external framebuffers."""

import unittest

import numpy as np

from tests.integration.support import SOLID_PRESET, assert_solid_frame, require_gl_tests

require_gl_tests("moderngl")

import moderngl

from python_projectm.integrations.moderngl import ModernGLRenderer


class ModernGLTests(unittest.TestCase):
    def setUp(self):
        self.context = moderngl.create_standalone_context(require=330)
        self.addCleanup(self.context.release)

    def test_texture_output_and_resize(self):
        with ModernGLRenderer(self.context, 96, 64, activate=lambda: self.context) as renderer:
            renderer.load_preset_data(SOLID_PRESET, smooth=False)
            renderer.add_pcm(np.zeros((512, 2), dtype=np.float32))
            texture = renderer.render()
            self.assertIs(texture, renderer.texture)
            with renderer.current():
                frame = np.frombuffer(texture.read(alignment=1), dtype=np.uint8).reshape(64, 96, 4)
            assert_solid_frame(self, frame, 96, 64)
            renderer.resize(80, 48)
            self.assertIsNot(renderer.texture, texture)
            self.assertEqual(renderer.texture.size, (80, 48))
            renderer.render()
            with renderer.current():
                frame = np.frombuffer(renderer.texture.read(alignment=1), dtype=np.uint8).reshape(48, 80, 4)
            assert_solid_frame(self, frame, 80, 48)
        renderer.close()

    def test_external_framebuffer_remains_usable_after_renderer_closes(self):
        with self.context:
            texture = self.context.texture((80, 48), components=4, dtype="f1")
            target = self.context.framebuffer(color_attachments=[texture])
            try:
                with ModernGLRenderer(self.context, 96, 64) as renderer:
                    renderer.load_preset_data(SOLID_PRESET, smooth=False)
                    self.assertIs(renderer.render(target), target)
                frame = np.frombuffer(target.read(components=4, alignment=1), dtype=np.uint8).reshape(48, 80, 4)
                assert_solid_frame(self, frame, 80, 48)
                target.clear(0.25, 0.5, 0.75, 1.0)
                pixel = np.frombuffer(texture.read(alignment=1), dtype=np.uint8)[:4]
                np.testing.assert_allclose(pixel, [64, 128, 191, 255], atol=1)
            finally:
                target.release()
                texture.release()
