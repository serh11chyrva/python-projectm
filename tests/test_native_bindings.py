"""ctypes symbol errors and ownership of allocated version strings."""

import ctypes
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from python_projectm.native import bindings
from python_projectm.native.errors import NativeError, NativeSymbolError


class NativeBindingTests(unittest.TestCase):
    def test_void_function_is_resolved_lazily_and_cached(self):
        function = Mock(return_value=None)
        library = SimpleNamespace(example=function)
        with patch.object(bindings, "_lib", library):
            bound = bindings._bind("example", argtypes=[ctypes.c_void_p])
            function.assert_not_called()
            bound(None)
            library.example = Mock(side_effect=AssertionError("Symbol was resolved again"))
            bound(None)
        self.assertIsNone(function.restype)
        self.assertEqual(function.argtypes, [ctypes.c_void_p])
        self.assertEqual(function.call_count, 2)

    def test_outdated_wrapper_has_an_actionable_error(self):
        with patch.object(bindings, "_lib", SimpleNamespace()):
            with self.assertRaisesRegex(NativeSymbolError, "Rebuild projectM and pypm_capi"):
                bindings._bind("missing_symbol")()

    def test_allocated_version_string_is_copied_and_freed(self):
        buffer = ctypes.create_string_buffer(b"4.1.6")
        pointer = ctypes.addressof(buffer)
        with patch.object(bindings, "pypm_clear_error"), \
                patch.object(bindings, "check_error"), \
                patch.object(bindings, "pypm_free_string") as free:
            result = bindings._owned_string(lambda: pointer)
        free.assert_called_once_with(pointer)
        buffer.value = b"other"
        self.assertEqual(result, b"4.1.6")

    def test_null_version_string_raises_without_freeing_null(self):
        with patch.object(bindings, "pypm_clear_error"), \
                patch.object(bindings, "check_error"), \
                patch.object(bindings, "pypm_free_string") as free:
            with self.assertRaises(NativeError):
                bindings._owned_string(lambda: None)
        free.assert_not_called()
