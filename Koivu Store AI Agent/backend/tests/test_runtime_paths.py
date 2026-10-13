import tempfile
import unittest
from pathlib import Path

from core.runtime_paths import resolve_frontend_directory


class ResolveFrontendDirectoryTests(unittest.TestCase):
    def test_finds_frontend_next_to_packaged_app_module(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            app_dir = Path(temp_dir) / "app"
            app_dir.mkdir()
            frontend_dir = app_dir / "frontend"
            frontend_dir.mkdir()

            self.assertEqual(resolve_frontend_directory(app_dir / "main.py"), frontend_dir)

    def test_finds_frontend_sibling_to_backend_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)
            backend_dir = project_dir / "backend"
            backend_dir.mkdir()
            frontend_dir = project_dir / "frontend"
            frontend_dir.mkdir()

            self.assertEqual(resolve_frontend_directory(backend_dir / "main.py"), frontend_dir)

    def test_raises_clear_error_when_frontend_is_missing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaisesRegex(RuntimeError, "Frontend assets directory not found"):
                resolve_frontend_directory(Path(temp_dir) / "backend" / "main.py")


if __name__ == "__main__":
    unittest.main()
