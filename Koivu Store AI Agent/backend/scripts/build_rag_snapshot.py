"""Package a stopped local Chroma index as a checksummed, versioned ZIP artifact."""

from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path


def build_snapshot(index_dir: Path, output: Path) -> None:
    index_dir = index_dir.resolve()
    output = output.resolve()
    if not (index_dir / "chroma.sqlite3").is_file():
        raise FileNotFoundError(f"No Chroma index database found in {index_dir}")
    files = sorted(path for path in index_dir.rglob("*") if path.is_file())
    if not files:
        raise ValueError("The Chroma index directory is empty")
    manifest = {
        "format_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "files": {
            path.relative_to(index_dir).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in files
        },
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in files:
            archive.write(path, path.relative_to(index_dir).as_posix())
        archive.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
    print(f"Created {output} with {len(files)} Chroma files")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", type=Path, default=Path(__file__).resolve().parents[1] / "chroma_db")
    parser.add_argument("--output", type=Path, required=True, help="Versioned .zip path outside the source tree")
    args = parser.parse_args()
    build_snapshot(args.index, args.output)


if __name__ == "__main__":
    main()
