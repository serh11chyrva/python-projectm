"""Reject invalid public arguments before they can reach native code."""

import unittest

import numpy as np

from python_projectm.core.validation import dimensions, encoded_text, integer, nonnegative


class ValidationTests(unittest.TestCase):
    def test_integer_accepts_numpy_indices_and_enforces_bounds(self):
        self.assertEqual(integer(np.int64(7), "size"), 7)
        for value in (0, -1, 2**31):
            with self.subTest(value=value), self.assertRaises(ValueError):
                integer(value, "size")
        for value in (True, 1.5, "3"):
            with self.subTest(value=value), self.assertRaises(TypeError):
                integer(value, "size")

    def test_only_core_dimensions_can_be_zero(self):
        self.assertEqual(dimensions(0, 64, allow_zero=True), (0, 64))
        with self.assertRaises(ValueError):
            dimensions(0, 64)
        with self.assertRaises(ValueError):
            dimensions(-1, 64, allow_zero=True)

    def test_parameters_must_be_finite_and_nonnegative(self):
        self.assertEqual(nonnegative(0), 0.0)
        self.assertEqual(nonnegative(1.25), 1.25)
        for value in (-1, np.inf, -np.inf, np.nan):
            with self.subTest(value=value), self.assertRaises(ValueError):
                nonnegative(value)

    def test_native_text_is_utf8_without_embedded_nul(self):
        self.assertEqual(encoded_text("caf\u00e9.milk", "path"), b"caf\xc3\xa9.milk")
        with self.assertRaises(ValueError):
            encoded_text("a\0b", "path")
        with self.assertRaises(TypeError):
            encoded_text(b"preset", "data")
