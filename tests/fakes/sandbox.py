"""FakeSandboxRunner: simulates §9.3 outcomes without Docker."""
from __future__ import annotations

from pathlib import Path
from typing import Literal

from aae.codebuilder.sandbox import SandboxResult


class FakeSandboxRunner:
    def __init__(
        self,
        *,
        mode: Literal["pass", "fail", "timeout", "oom", "network_blocked"] = "pass",
        stdout: str | None = None,
    ) -> None:
        self.mode = mode
        self._stdout = stdout
        self.calls: list[Path] = []

    def run(self, job_dir: Path, *, wall_seconds: int = 300) -> SandboxResult:
        self.calls.append(job_dir)
        if self.mode == "pass":
            return SandboxResult(
                exit_code=0,
                stdout=self._stdout or "2 passed in 0.01s\nTOTAL  100%\n",
                stderr="",
                wall_seconds=0.1,
                reason="ok",
            )
        if self.mode == "fail":
            return SandboxResult(
                exit_code=1,
                stdout=self._stdout or "1 failed, 1 passed\n",
                stderr="AssertionError",
                wall_seconds=0.1,
                reason="error",
            )
        if self.mode == "timeout":
            return SandboxResult(
                exit_code=124,
                stdout="",
                stderr="timeout",
                wall_seconds=float(wall_seconds),
                reason="timeout",
            )
        if self.mode == "oom":
            return SandboxResult(
                exit_code=137,
                stdout="",
                stderr="Out of memory",
                wall_seconds=2.0,
                reason="oom",
            )
        # network_blocked
        return SandboxResult(
            exit_code=1,
            stdout="",
            stderr="socket.gaierror: [Errno -3] Temporary failure in name resolution",
            wall_seconds=0.1,
            reason="network_blocked",
        )
