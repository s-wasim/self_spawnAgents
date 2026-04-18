"""Hardened Docker sandbox runner (§9.3).

Wraps the frozen `docker run` command. A Protocol interface lets tests inject
a fake runner that simulates network-block, OOM, and timeout without Docker.
"""
from __future__ import annotations

import shlex
import subprocess
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass
class SandboxResult:
    exit_code: int
    stdout: str
    stderr: str
    wall_seconds: float
    reason: str = ""  # "ok" | "timeout" | "oom" | "network_blocked" | "error"


class SandboxRunner(Protocol):
    def run(self, job_dir: Path, *, wall_seconds: int = 300) -> SandboxResult: ...


FROZEN_DOCKER_ARGS: tuple[str, ...] = (
    "docker", "run", "--rm",
    "--runtime=runsc",
    "--network=none",
    "--read-only",
    "--tmpfs", "/tmp:rw,noexec,nosuid,size=64m",
    "--tmpfs", "/home/sandbox:rw,noexec,nosuid,size=16m",
    "--memory=512m", "--memory-swap=512m",
    "--cpus=1.0",
    "--pids-limit=128",
    "--ulimit", "nofile=256:256",
    "--ulimit", "nproc=64:64",
    "--security-opt=no-new-privileges:true",
    "--cap-drop=ALL",
    "--user", "1000:1000",
    "--workdir", "/home/sandbox",
    "--stop-timeout", "5",
)


def build_docker_command(job_dir: Path, *, wall_seconds: int = 300, name: str | None = None) -> list[str]:
    """Deterministic argv for §9.3; pure function so tests can assert it."""
    container_name = name or f"codebuilder-{uuid.uuid4()}"
    return [
        *FROZEN_DOCKER_ARGS[:2],  # docker run
        "--name", container_name,
        *FROZEN_DOCKER_ARGS[2:],
        "-v", f"{job_dir}:/home/sandbox:ro",
        "python:3.12-slim",
        "timeout", "-s", "KILL", str(wall_seconds),
        "python", "-m", "pytest", "-q", "/home/sandbox/test_tool.py",
    ]


class DockerSandboxRunner:
    """Production runner: invokes the frozen docker command via subprocess."""

    def __init__(self, *, binary: str = "docker") -> None:
        self._binary = binary

    def run(self, job_dir: Path, *, wall_seconds: int = 300) -> SandboxResult:
        import time
        argv = build_docker_command(job_dir, wall_seconds=wall_seconds)
        if self._binary != "docker":
            argv[0] = self._binary
        t0 = time.monotonic()
        try:
            proc = subprocess.run(
                argv,
                capture_output=True,
                text=True,
                timeout=wall_seconds + 30,
                check=False,
            )
            elapsed = time.monotonic() - t0
            reason = "ok" if proc.returncode == 0 else "error"
            # exit 137 = SIGKILL (timeout); 139 = SIGSEGV; 124 = GNU timeout
            if proc.returncode in (124, 137):
                reason = "timeout"
            return SandboxResult(
                exit_code=proc.returncode,
                stdout=proc.stdout,
                stderr=proc.stderr,
                wall_seconds=elapsed,
                reason=reason,
            )
        except subprocess.TimeoutExpired as e:
            return SandboxResult(
                exit_code=124,
                stdout=(e.stdout or b"").decode(errors="replace") if isinstance(e.stdout, bytes) else (e.stdout or ""),
                stderr=f"host-level timeout after {wall_seconds + 30}s",
                wall_seconds=time.monotonic() - t0,
                reason="timeout",
            )

    def command_preview(self, job_dir: Path, *, wall_seconds: int = 300) -> str:
        return " ".join(shlex.quote(a) for a in build_docker_command(job_dir, wall_seconds=wall_seconds))
