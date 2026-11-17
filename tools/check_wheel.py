"""Inspect release wheel contents and metadata without importing the package."""

import argparse
import struct
import tomllib
import zipfile
from email.parser import BytesParser
from pathlib import Path, PurePosixPath

from packaging.specifiers import SpecifierSet
from packaging.tags import parse_tag
from packaging.utils import parse_wheel_filename
from trove_classifiers import classifiers, deprecated_classifiers


ROOT = Path(__file__).resolve().parents[1]

# These are Windows OS libraries, not redistributable C++ runtime dependencies.
WINDOWS_SYSTEM_DLLS = {
    "advapi32.dll", "bcrypt.dll", "comctl32.dll", "comdlg32.dll", "crypt32.dll",
    "gdi32.dll", "glu32.dll", "imm32.dll", "kernel32.dll", "msvcrt.dll",
    "normaliz.dll", "ntdll.dll", "ole32.dll", "oleaut32.dll", "opengl32.dll",
    "psapi.dll", "rpcrt4.dll", "secur32.dll", "setupapi.dll", "shell32.dll",
    "shlwapi.dll", "ucrtbase.dll", "user32.dll", "version.dll", "winmm.dll",
    "winspool.drv", "ws2_32.dll",
}


def check_windows_dependencies(wheel: zipfile.ZipFile, names: list[str]) -> None:
    import pefile

    libraries = {PurePosixPath(name).name.lower(): name for name in names if name.lower().endswith(".dll")}
    for filename in libraries.values():
        with pefile.PE(data=wheel.read(filename), fast_load=True) as image:
            image.parse_data_directories(directories=[
                pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_IMPORT"],
                pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_DELAY_IMPORT"],
            ])
            for entry in (*getattr(image, "DIRECTORY_ENTRY_IMPORT", ()), *getattr(image, "DIRECTORY_ENTRY_DELAY_IMPORT", ())):
                dependency = entry.dll.decode("ascii").lower()
                if dependency not in libraries and dependency not in WINDOWS_SYSTEM_DLLS and not dependency.startswith(("api-ms-", "ext-ms-")):
                    raise ValueError(f"Unbundled Windows dependency: {filename} -> {dependency}")


def check(path: Path) -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    _, version, _, tags = parse_wheel_filename(path.name)
    if str(version) != project["version"]:
        raise ValueError(f"Wrong release version: {path}")
    platforms = {tag.platform for tag in tags}
    if platforms != {"win_amd64"}:
        raise ValueError(f"Unexpected platform tags: {tags}")
    if any(tag.interpreter != "py3" or tag.abi != "none" for tag in tags):
        raise ValueError(f"Expected Python ABI-independent platform tags: {tags}")
    with zipfile.ZipFile(path) as wheel:
        names = wheel.namelist()
        metadata_paths = [name for name in names if name.endswith(".dist-info/METADATA")]
        if len(metadata_paths) != 1:
            raise ValueError("Expected exactly one distribution metadata directory")
        dist_info = metadata_paths[0].removesuffix("METADATA")
        metadata = BytesParser().parsebytes(wheel.read(metadata_paths[0]))
        wheel_metadata = BytesParser().parsebytes(wheel.read(dist_info + "WHEEL"))
        if metadata["Name"] != project["name"] or SpecifierSet(metadata["Requires-Python"]) != SpecifierSet(project["requires-python"]):
            raise ValueError("Unexpected package name or Python requirement")
        wheel_classifiers = set(metadata.get_all("Classifier", []))
        if wheel_classifiers != set(project["classifiers"]):
            raise ValueError("Wheel classifiers differ from the project metadata")
        invalid_classifiers = wheel_classifiers - classifiers
        if invalid_classifiers:
            raise ValueError(f"Invalid PyPI classifiers: {sorted(invalid_classifiers)}")
        deprecated = wheel_classifiers & deprecated_classifiers.keys()
        if deprecated:
            raise ValueError(f"Deprecated PyPI classifiers: {sorted(deprecated)}")
        if " ".join(str(metadata["License-Expression"]).split()) != project["license"]:
            raise ValueError("Missing or incorrect SPDX license expression")
        if "text/markdown" not in metadata.get("Description-Content-Type", ""):
            raise ValueError("The PyPI description must be Markdown")
        project_urls = {" ".join(str(value).split()) for value in metadata.get_all("Project-URL", [])}
        if "Documentation, " + project["urls"]["Documentation"] not in project_urls:
            raise ValueError("The documentation URL is missing")
        recorded_tags = set().union(*(parse_tag(tag) for tag in wheel_metadata.get_all("Tag", [])))
        if recorded_tags != set(tags) or wheel_metadata["Root-Is-Purelib"] != "false":
            raise ValueError("Wheel filename and metadata tags disagree, or wheel is marked pure")
        for license_file in ("LICENSE", "THIRD_PARTY_NOTICES.md", *("licenses/" + p.name for p in (ROOT / "licenses").glob("*.txt"))):
            if dist_info + "licenses/" + license_file not in names:
                raise ValueError(f"Missing license file: {license_file}")
        for required in ("python_projectm/presets/pulse.milk", "python_projectm/native/native-build.txt", "python_projectm/native/bin/__init__.py"):
            if required not in names:
                raise ValueError(f"Missing package resource: {required}")
        native = [name for name in names if name.startswith("python_projectm/native/bin/")]
        required_libraries = ("pypm_capi.dll", "projectM-4.dll", "glew32.dll", "msvcp140.dll")
        for library in required_libraries:
            if "python_projectm/native/bin/" + library not in native:
                raise ValueError(f"Missing bundled native library: {library}")
        for name in names:
            suffix = PurePosixPath(name).suffix
            if suffix in {".lib", ".a", ".exp", ".pdb", ".obj", ".pyc", ".h", ".hpp"} or "/__pycache__/" in name:
                raise ValueError(f"Build-only file in wheel: {name}")
            if suffix == ".dll":
                data = wheel.read(name)
                offset = struct.unpack_from("<I", data, 0x3C)[0]
                if data[:2] != b"MZ" or data[offset:offset + 4] != b"PE\0\0" or struct.unpack_from("<H", data, offset + 4)[0] != 0x8664:
                    raise ValueError(f"Not an x64 PE library: {name}")
            if ".so" in PurePosixPath(name).name or suffix == ".dylib":
                raise ValueError(f"Non-Windows native library in release wheel: {name}")
        check_windows_dependencies(wheel, names)
    print(f"Validated {path.name}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wheels", nargs="+", type=Path)
    args = parser.parse_args()
    for wheel_path in args.wheels:
        check(wheel_path)
