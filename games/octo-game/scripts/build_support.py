"""Shared helpers for Octo Game build scripts."""

from pathlib import Path
import os
import shutil


def resolve_dasm(game_root: Path) -> Path:
    """Find DASM in an explicit setting, local tools, or PATH."""
    configured = os.environ.get("DASM")
    candidates = [
        Path(configured) if configured else None,
        game_root / "resources" / "tools" / "dasm-2.20.17" / "dasm",
        game_root.parent.parent / "resources" / "tools" / "dasm-2.20.17" / "dasm",
        Path(shutil.which("dasm")) if shutil.which("dasm") else None,
    ]
    for candidate in candidates:
        if candidate is not None and candidate.is_file():
            return candidate
    raise SystemExit("error: DASM not found; install dasm or set DASM=/path/to/dasm")
