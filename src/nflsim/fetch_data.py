"""Stage 1: download nflverse raw files into data/raw (idempotent)."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import requests

from .config import RAW, RAW_FILES


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch(force: bool = False) -> dict:
    RAW.mkdir(parents=True, exist_ok=True)
    manifest = {}
    for name, url in RAW_FILES.items():
        dest = RAW / name
        if dest.exists() and not force:
            print(f"skip   {name} (exists)")
        else:
            print(f"fetch  {name}")
            with requests.get(url, stream=True, timeout=600) as r:
                r.raise_for_status()
                with dest.open("wb") as f:
                    for chunk in r.iter_content(1 << 20):
                        f.write(chunk)
        manifest[name] = {"url": url, "bytes": dest.stat().st_size, "sha256": sha256(dest)}
    (RAW / "manifest.json").write_text(json.dumps(manifest, indent=2))
    return manifest


if __name__ == "__main__":
    fetch(force="--force" in sys.argv)
