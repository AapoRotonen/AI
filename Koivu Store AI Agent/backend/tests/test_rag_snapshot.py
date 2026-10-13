"""Local filesystem-only integrity tests for the Chroma snapshot format."""

import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from core.rag_snapshot import _verify_and_extract
from scripts.build_rag_snapshot import build_snapshot


class RagSnapshotTests(unittest.TestCase):
    def test_snapshot_round_trip_verifies_manifest_and_chroma_database(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            source.mkdir()
            (source / "chroma.sqlite3").write_bytes(b"local test index")
            (source / "segment.bin").write_bytes(b"segment data")
            archive = root / "snapshot.zip"
            destination = root / "restored"

            build_snapshot(source, archive)
            _verify_and_extract(archive, destination)

            self.assertEqual((destination / "chroma.sqlite3").read_bytes(), b"local test index")
            self.assertEqual((destination / "segment.bin").read_bytes(), b"segment data")

    def test_snapshot_rejects_manifest_hash_mismatch(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = root / "broken.zip"
            manifest = {"format_version": 1, "files": {"chroma.sqlite3": "0" * 64}}
            with zipfile.ZipFile(archive, "w") as output:
                output.writestr("chroma.sqlite3", b"index")
                output.writestr("manifest.json", json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, "SHA-256"):
                _verify_and_extract(archive, root / "restored")

    def test_snapshot_rejects_zip_slip_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = root / "unsafe.zip"
            manifest = {"format_version": 1, "files": {"../escape": "0" * 64}}
            with zipfile.ZipFile(archive, "w") as output:
                output.writestr("../escape", b"no")
                output.writestr("manifest.json", json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, "unsafe file path"):
                _verify_and_extract(archive, root / "restored")
            self.assertFalse((root.parent / "escape").exists())


if __name__ == "__main__":
    unittest.main()
