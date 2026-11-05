"""Fetch the pinned example media into a Pages build without tracking binaries."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from urllib.request import urlopen


def fetch_examples(manifest_path: Path, output: Path) -> None:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    base = f'https://huggingface.co/datasets/{manifest["repository"]}/resolve/{manifest["revision"]}'
    for asset in manifest["assets"]:
        relative = Path(asset["path"])
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError(f"Unsafe asset path: {relative}")
        target = output / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        digest = hashlib.sha256()
        try:
            with urlopen(f"{base}/{relative.as_posix()}", timeout=120) as response, target.open("wb") as stream:
                while chunk := response.read(1024 * 1024):
                    digest.update(chunk)
                    stream.write(chunk)
            if digest.hexdigest() != asset["sha256"]:
                raise ValueError(f"SHA-256 mismatch: {relative}")
        except Exception:
            target.unlink(missing_ok=True)
            raise
        print(f"Verified {relative}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=Path("paper_site/examples-media.json"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    fetch_examples(args.manifest, args.output)
