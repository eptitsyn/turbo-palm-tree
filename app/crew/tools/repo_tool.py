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


def list_repository_files(
    repo_path: str | Path, *, max_files: int = 5000, include_hidden: bool = False
) -> dict[str, Any]:
    """
    Return a (bounded) list of repo files relative to repo root.
    Skips .git and hidden files unless include_hidden=True.
    """
    root = Path(repo_path)
    if not root.exists():
        return {"status": "error", "error": f"Path not found: {repo_path}"}

    files: list[str] = []
    for path in root.rglob("*"):
        if ".git" in path.parts:
            continue
        if path.is_dir():
            continue
        rel = path.relative_to(root)
        if not include_hidden and any(part.startswith(".") for part in rel.parts):
            continue
        files.append(str(rel))
        if len(files) >= max_files:
            break
    return {"status": "ok", "files": files, "count": len(files), "truncated": len(files) >= max_files}


def extract_python_signatures(file_path: str | Path) -> dict[str, Any]:
    """
    Extract function/method/class signatures from a Python file for lightweight context.
    """
    import ast

    path = Path(file_path)
    if not path.exists():
        return {"status": "error", "error": f"File not found: {file_path}"}
    try:
        source = path.read_text(encoding="utf-8")
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "error": f"Cannot read file: {exc}"}

    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return {"status": "error", "error": f"Syntax error parsing file: {exc}"}

    signatures: list[dict[str, Any]] = []

    def _args_to_str(node: ast.arguments) -> str:
        parts = []
        for arg in node.posonlyargs:
            parts.append(arg.arg)
        for arg in node.args:
            parts.append(arg.arg)
        if node.vararg:
            parts.append(f"*{node.vararg.arg}")
        if node.kwonlyargs:
            for arg in node.kwonlyargs:
                parts.append(f"{arg.arg}=")
        if node.kwarg:
            parts.append(f"**{node.kwarg.arg}")
        return ", ".join(parts)

    class _Visitor(ast.NodeVisitor):
        def visit_FunctionDef(self, node: ast.FunctionDef) -> Any:
            signatures.append(
                {"kind": "function", "name": node.name, "args": _args_to_str(node.args)}
            )
            self.generic_visit(node)

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> Any:
            signatures.append(
                {"kind": "async_function", "name": node.name, "args": _args_to_str(node.args)}
            )
            self.generic_visit(node)

        def visit_ClassDef(self, node: ast.ClassDef) -> Any:
            bases = [getattr(base, "id", getattr(base, "attr", "unknown")) for base in node.bases]
            signatures.append({"kind": "class", "name": node.name, "bases": bases})
            self.generic_visit(node)

    _Visitor().visit(tree)
    return {"status": "ok", "signatures": signatures}
