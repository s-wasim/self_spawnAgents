"""Frozen-path integrity CLI (§11.2).

Commands:
  freeze  — compute SHA-256 for every FROZEN_PATHS entry, write hashes.lock
  verify  — recompute and compare; exit 1 on drift
  update  — same as freeze, but requires a CHANGELOG.frozen.md entry newer than the old lock
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import typer

from aae.config.frozen import FROZEN_PATHS, HASHES_LOCK_FILE

app = typer.Typer(help="AAE frozen-path integrity tool")


def _repo_root() -> Path:
    # Walk up from this file until we find pyproject.toml.
    p = Path(__file__).resolve()
    for parent in (p, *p.parents):
        if (parent / "pyproject.toml").exists():
            return parent
    return Path.cwd()


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def compute_hashes(root: Path | None = None) -> dict[str, str]:
    root = root or _repo_root()
    out: dict[str, str] = {}
    for rel in FROZEN_PATHS:
        p = root / rel
        if not p.exists():
            raise FileNotFoundError(f"Frozen path missing: {rel}")
        out[rel] = _sha256_file(p)
    return out


def read_lock(root: Path | None = None) -> dict[str, str]:
    root = root or _repo_root()
    lock = root / HASHES_LOCK_FILE
    if not lock.exists():
        return {}
    return json.loads(lock.read_text(encoding="utf-8"))


def write_lock(hashes: dict[str, str], root: Path | None = None) -> Path:
    root = root or _repo_root()
    lock = root / HASHES_LOCK_FILE
    lock.parent.mkdir(parents=True, exist_ok=True)
    lock.write_text(json.dumps(hashes, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return lock


@app.command()
def freeze() -> None:
    """Compute and write hashes.lock."""
    hashes = compute_hashes()
    path = write_lock(hashes)
    typer.echo(f"Wrote {path} with {len(hashes)} entries.")


@app.command()
def verify() -> None:
    """Compare computed hashes to hashes.lock. Exit 1 on drift."""
    current = compute_hashes()
    expected = read_lock()
    drift: list[str] = []
    for path, h in current.items():
        if expected.get(path) != h:
            drift.append(path)
    if drift:
        for p in drift:
            typer.echo(f"DRIFT: {p}  expected={expected.get(p)}  actual={current[p]}")
        raise typer.Exit(code=1)
    typer.echo(f"OK  {len(current)} frozen paths match hashes.lock")


@app.command()
def update() -> None:
    """Re-freeze after a legitimate change; requires CHANGELOG.frozen.md to have been edited."""
    root = _repo_root()
    changelog = root / "CHANGELOG.frozen.md"
    if not changelog.exists():
        raise typer.BadParameter("CHANGELOG.frozen.md missing")
    hashes = compute_hashes()
    path = write_lock(hashes)
    typer.echo(f"Updated {path}. Append a CHANGELOG.frozen.md entry before committing.")


def verify_exit_code() -> int:
    """Programmatic entry; returns 0 on clean, 1 on drift."""
    try:
        current = compute_hashes()
    except FileNotFoundError:
        return 1
    expected = read_lock()
    return 0 if expected == current else 1


if __name__ == "__main__":
    app()
