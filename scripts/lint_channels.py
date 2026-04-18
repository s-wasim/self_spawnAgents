"""Lint: ensure `import httpx` / `import requests` appears only in aae/channels/ (§5.1 rule 8).

CI gate. Exit 0 on clean, 1 with violations printed.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

FORBIDDEN = {"httpx", "requests"}
ALLOWED_DIR = Path("aae") / "channels"


def _is_forbidden_import(node: ast.AST) -> bool:
    if isinstance(node, ast.Import):
        return any(alias.name.split(".")[0] in FORBIDDEN for alias in node.names)
    if isinstance(node, ast.ImportFrom):
        root = (node.module or "").split(".")[0]
        return root in FORBIDDEN
    return False


def scan_file(path: Path) -> list[tuple[int, str]]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError:
        return []
    out: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if _is_forbidden_import(node):
            out.append((getattr(node, "lineno", 0), ast.unparse(node)))
    return out


def scan_tree(root: Path) -> list[tuple[Path, int, str]]:
    violations: list[tuple[Path, int, str]] = []
    aae_root = root / "aae"
    if not aae_root.exists():
        return violations
    for py in aae_root.rglob("*.py"):
        try:
            rel_parts = py.relative_to(root).parts
        except ValueError:
            continue
        # aae/channels/*.py is allowed
        if len(rel_parts) >= 2 and rel_parts[0] == "aae" and rel_parts[1] == "channels":
            continue
        for lineno, src in scan_file(py):
            violations.append((py, lineno, src))
    return violations


def main(root: str = ".") -> int:
    r = Path(root).resolve()
    violations = scan_tree(r)
    if violations:
        print("channel-lint FAILED: forbidden httpx/requests imports outside aae/channels/", file=sys.stderr)
        for path, lineno, src in violations:
            print(f"  {path}:{lineno}: {src}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else "."))
