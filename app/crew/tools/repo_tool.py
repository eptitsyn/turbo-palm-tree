# app/crew/tools/repo_tool.py
from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any


def clone_repository(
    repo_url: str,
    *,
    ref: str | None = None,
    dest_dir: str | None = None,
    depth: int = 1,
    timeout: float = 30.0,
) -> dict[str, Any]:
    """
    Clone a repository to a temp directory (or provided dest) and optionally checkout a ref.
    Returns path and status for agent use. Uses shallow clone by default.
    """
    dest = Path(dest_dir) if dest_dir else Path(tempfile.mkdtemp(prefix="repo_clone_"))
    cmd = ["git", "clone", "--depth", str(depth), repo_url, str(dest)]
    try:
        subprocess.run(cmd, check=True, timeout=timeout, capture_output=True)
        if ref:
            subprocess.run(
                ["git", "-C", str(dest), "checkout", ref],
                check=True,
                timeout=timeout,
                capture_output=True,
            )
        return {"status": "ok", "path": str(dest)}
    except Exception as exc:  # noqa: BLE001
        # Cleanup on failure if we created the dir
        if dest_dir is None and dest.exists():
            shutil.rmtree(dest, ignore_errors=True)
        return {"status": "error", "error": str(exc)}
