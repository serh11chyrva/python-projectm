"""Shared rendering assertions with an original, texture-free test preset."""

import importlib
import os
import time
import unittest

import numpy as np


SOLID_PRESET = """MILKDROP_PRESET_VERSION=201
PSVERSION_WARP=0
PSVERSION_COMP=2
[preset00]
fDecay=0
fGammaAdj=1
fWaveAlpha=0
comp_1=`shader_body
comp_2=`{
comp_3=`ret = float3(0.2, 0.4, 0.8);
comp_4=`}
"""


def require_gl_tests(*dependencies):
    if os.environ.get("PYTHON_PROJECTM_RUN_GL_TESTS") != "1":
        raise unittest.SkipTest("Set PYTHON_PROJECTM_RUN_GL_TESTS=1 to run real OpenGL tests")
    for name in dependencies:
        try:
            importlib.import_module(name)
        except ModuleNotFoundError as error:
            if error.name == name:
                raise unittest.SkipTest(f"Optional dependency {name} is not installed") from error
            raise


def assert_solid_frame(test, frame, width, height):
    test.assertEqual(frame.shape, (height, width, 4))
    test.assertEqual(frame.dtype, np.uint8)
    test.assertTrue(frame.flags.c_contiguous)
    # A known color catches empty output and accidental rendering to framebuffer zero.
    center = frame[height // 4:3 * height // 4, width // 4:3 * width // 4, :3]
    expected = np.broadcast_to([51, 102, 204], center.shape)
    np.testing.assert_allclose(center.astype(float), expected, atol=4, rtol=0)


def wait_until(app, predicate, timeout=10.0):
    deadline = time.monotonic() + timeout
    while not predicate():
        app.processEvents()
        if time.monotonic() >= deadline:
            raise AssertionError("Timed out waiting for a Qt rendering event")
        time.sleep(0.01)


def image_array(image):
    from PySide6.QtGui import QImage

    image = image.convertToFormat(QImage.Format.Format_RGBA8888)
    rows = np.frombuffer(image.bits(), dtype=np.uint8).reshape(image.height(), image.bytesPerLine())
    return rows[:, :image.width() * 4].reshape(image.height(), image.width(), 4).copy()
