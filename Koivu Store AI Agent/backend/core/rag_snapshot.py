"""Download and verify the immutable Chroma snapshot used by cloud instances."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import tempfile
import zipfile
from pathlib import Path, PurePosixPath


MAX_SNAPSHOT_BYTES = 500 * 1024 * 1024


def _verify_and_extract(archive_path: Path, destination: Path) -> None:
    if not zipfile.is_zipfile(archive_path):
        raise ValueError("RAG snapshot is not a ZIP archive")

    with zipfile.ZipFile(archive_path) as archive:
        entries = archive.infolist()
        manifest_entry = next((entry for entry in entries if entry.filename == "manifest.json"), None)
        if manifest_entry is None or manifest_entry.file_size > 1024 * 1024:
            raise ValueError("RAG snapshot has no valid manifest")
        manifest = json.loads(archive.read(manifest_entry))
        if manifest.get("format_version") != 1 or not isinstance(manifest.get("files"), dict):
            raise ValueError("Unsupported RAG snapshot manifest")

        total_size = sum(entry.file_size for entry in entries)
        if total_size > MAX_SNAPSHOT_BYTES:
            raise ValueError("RAG snapshot exceeds the configured extraction limit")

        destination.parent.mkdir(parents=True, exist_ok=True)
        staging = Path(tempfile.mkdtemp(prefix="koivu-rag-", dir=destination.parent))
        try:
            for entry in entries:
                if entry.is_dir() or entry.filename == "manifest.json":
                    continue
                relative = PurePosixPath(entry.filename)
                if relative.is_absolute() or ".." in relative.parts or not relative.parts:
                    raise ValueError("RAG snapshot contains an unsafe file path")
                if stat.S_ISLNK(entry.external_attr >> 16):
                    raise ValueError("RAG snapshot must not contain symbolic links")
                target = staging.joinpath(*relative.parts)
                target.parent.mkdir(parents=True, exist_ok=True)
                digest = hashlib.sha256()
                with archive.open(entry) as source, target.open("wb") as output:
                    while block := source.read(1024 * 1024):
                        output.write(block)
                        digest.update(block)
                expected = manifest["files"].get(relative.as_posix())
                if expected is None or digest.hexdigest() != expected:
                    raise ValueError("RAG snapshot file failed its SHA-256 check")

            if set(manifest["files"]) != {
                entry.filename for entry in entries if not entry.is_dir() and entry.filename != "manifest.json"
            }:
                raise ValueError("RAG snapshot manifest does not match its archive contents")
            if not (staging / "chroma.sqlite3").is_file():
                raise ValueError("RAG snapshot is missing Chroma's database file")

            if destination.exists():
                shutil.rmtree(destination)
            os.replace(staging, destination)
        finally:
            if staging.exists():
                shutil.rmtree(staging, ignore_errors=True)


def restore_rag_snapshot(blob_url: str, destination: str | Path, managed_identity_client_id: str = "") -> None:
    """Restore the private Blob ZIP with managed identity and no account keys/SAS tokens."""
    if not blob_url.startswith("https://") or "?" in blob_url:
        raise ValueError("RAG snapshot URL must be HTTPS and must not contain a SAS query")

    from azure.identity import DefaultAzureCredential
    from azure.storage.blob import BlobClient

    credential = DefaultAzureCredential(
        managed_identity_client_id=managed_identity_client_id or None,
        exclude_interactive_browser_credential=True,
    )
    archive_path = None
    try:
        blob = BlobClient.from_blob_url(blob_url, credential=credential)
        properties = blob.get_blob_properties()
        if properties.size > MAX_SNAPSHOT_BYTES:
            raise ValueError("RAG snapshot exceeds the configured download limit")
        with tempfile.NamedTemporaryFile(prefix="koivu-rag-", suffix=".zip", delete=False) as temp_file:
            archive_path = Path(temp_file.name)
            blob.download_blob().readinto(temp_file)
        _verify_and_extract(archive_path, Path(destination))
    finally:
        if archive_path is not None:
            archive_path.unlink(missing_ok=True)
        credential.close()
