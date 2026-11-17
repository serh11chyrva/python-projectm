"""Prepare verified native release sources before creating a release source bundle."""

import argparse
import hashlib
import json
import tarfile
import tempfile
from pathlib import Path
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parents[1]


def prepare(output: Path) -> None:
    sources = json.loads((ROOT / "native-sources.json").read_text(encoding="utf-8"))
    output.mkdir(parents=True, exist_ok=True)
    for name in ("projectm", "glew"):
        source = sources[name]
        destination = output / source["directory"]
        # Never replace an existing upstream tree, including local modifications.
        if destination.exists():
            raise FileExistsError(f"{destination} already exists; use a fresh output directory")
        algorithm = "sha256" if "sha256" in source else "sha512"
        digest = hashlib.new(algorithm)
        print(f"Downloading {source['url']}", flush=True)
        with tempfile.TemporaryFile() as download:
            with urlopen(source["url"], timeout=120) as response:
                while chunk := response.read(1024 * 1024):
                    digest.update(chunk)
                    download.write(chunk)
            if digest.hexdigest() != source[algorithm]:
                raise ValueError(f"{name} {algorithm} mismatch; refusing to extract")
            download.seek(0)
            with tarfile.open(fileobj=download, mode="r:gz") as archive:
                # Each archive must contain precisely its documented top-level tree.
                if any(Path(member.name).parts[0] != source["directory"] for member in archive):
                    raise ValueError(f"Unexpected top-level directory in {name} archive")
                archive.extractall(output, filter="data")
        print(f"Prepared {destination}", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT)
    prepare(parser.parse_args().output.resolve())
