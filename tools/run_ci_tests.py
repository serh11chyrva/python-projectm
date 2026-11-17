"""Run existing unittest suites; require every rendering suite in integration CI."""

import argparse
import importlib
import os
import sys
import unittest
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--integration", action="store_true")
    args = parser.parse_args()
    root = Path.cwd().resolve()
    sys.path.insert(0, str(root))
    if args.integration:
        os.environ["PYTHON_PROJECTM_RUN_GL_TESTS"] = "1"
        os.environ.pop("PYTHON_PROJECTM_LIBRARY", None)
        for name in ("glfw", "moderngl", "PySide6"):
            importlib.import_module(name)
        import python_projectm
        from python_projectm.core.version import get_version_string

        installed = Path(python_projectm.__file__).resolve()
        if installed.is_relative_to(root) or not installed.is_relative_to(Path(sys.prefix).resolve()):
            raise RuntimeError(f"Expected the installed wheel, imported {installed}")
        version = get_version_string()
        if "4.1.6" not in version:
            raise RuntimeError(f"Unexpected native version: {version}")
        print(f"Installed package: {installed}\nNative version: {version}", flush=True)
        suite = unittest.defaultTestLoader.discover("tests", top_level_dir=".")
    else:
        os.environ.pop("PYTHON_PROJECTM_RUN_GL_TESTS", None)
        suite = unittest.TestSuite(
            unittest.defaultTestLoader.discover("tests", pattern=pattern, top_level_dir=".")
            for pattern in ("test_audio.py", "test_example_audio.py", "test_native_bindings.py", "test_validation.py")
        )
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if args.integration and result.skipped:
        print(f"Unexpected skips in required integration tests: {result.skipped}", file=sys.stderr)
        return 1
    return 0 if result.wasSuccessful() and result.testsRun else 1


if __name__ == "__main__":
    raise SystemExit(main())
