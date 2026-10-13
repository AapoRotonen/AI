"""Resolve runtime asset paths for source checkouts and container images."""

from pathlib import Path


def resolve_frontend_directory(module_file: str | Path) -> Path:
    """Find frontend assets beside the app module or beside its backend folder."""
    module_dir = Path(module_file).resolve().parent
    candidates = (module_dir / "frontend", module_dir.parent / "frontend")
    for candidate in candidates:
        if candidate.is_dir():
            return candidate
    checked = ", ".join(str(path) for path in candidates)
    raise RuntimeError(f"Frontend assets directory not found; checked: {checked}")
