from __future__ import annotations

import base64
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .errors import P11Reason, SecError
from .http import SecResponse, validate_sec_url


SEC_RUNTIME_VERSION = "p11-sec-stdlib-runtime-v1"


@dataclass(frozen=True, slots=True)
class SecRuntimeDescriptor:
    project_root: Path
    python_executable: Path
    runner_script: Path
    runtime_version: str = SEC_RUNTIME_VERSION

    @classmethod
    def for_project(cls, project_root: str | Path) -> "SecRuntimeDescriptor":
        root = Path(project_root).expanduser().resolve()
        configured = os.environ.get("FFDF_SEC_PYTHON", "").strip()
        python_executable = Path(configured).expanduser().resolve() if configured else Path(sys.executable).resolve()
        runner_script = Path(__file__).resolve().with_name("runner.py")
        if not runner_script.is_file():
            raise FileNotFoundError(runner_script)
        return cls(root, python_executable, runner_script)

    def argv(self, operation: str) -> list[str]:
        if operation not in {"fetch", "doctor"}:
            raise ValueError(f"unsupported SEC runner operation: {operation}")
        return [str(self.python_executable), str(self.runner_script), operation]


def run_sec_runner(
    descriptor: SecRuntimeDescriptor,
    operation: str,
    payload: dict[str, Any] | None = None,
    *,
    timeout_seconds: float = 120.0,
) -> dict[str, Any]:
    body = json.dumps(payload or {}, ensure_ascii=False, separators=(",", ":"))
    try:
        completed = subprocess.run(
            descriptor.argv(operation),
            input=body,
            capture_output=True,
            text=True,
            encoding="utf-8",
            cwd=str(descriptor.project_root),
            shell=False,
            check=False,
            timeout=timeout_seconds,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise SecError(P11Reason.P11_SEC_DISCOVERY_FAILED, f"SEC runtime invocation failed: {exc}", retryable=True) from exc
    try:
        result = json.loads(completed.stdout)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SecError(P11Reason.P11_SEC_DISCOVERY_FAILED, "SEC runtime returned invalid JSON") from exc
    if not isinstance(result, dict):
        raise SecError(P11Reason.P11_SEC_DISCOVERY_FAILED, "SEC runtime response is not an object")
    if completed.returncode != 0 or result.get("status") == "ERROR":
        raise SecError(
            str(result.get("reason_code") or P11Reason.P11_SEC_DISCOVERY_FAILED.value),
            str(result.get("message") or completed.stderr or "SEC runtime failed"),
        )
    return result


class SecSubprocessTransport:
    def __init__(self, descriptor: SecRuntimeDescriptor) -> None:
        self.descriptor = descriptor

    @staticmethod
    def validate_url(url: str) -> str:
        return validate_sec_url(url)

    def fetch(
        self,
        url: str,
        headers: dict[str, str],
        timeout: float,
        *,
        max_bytes: int,
        max_redirects: int = 3,
        read_timeout: float | None = None,
        total_timeout: float | None = None,
    ) -> SecResponse:
        validate_sec_url(url)
        result = run_sec_runner(
            self.descriptor,
            "fetch",
            {
                "url": url,
                "headers": headers,
                "timeout": timeout,
                "read_timeout": read_timeout if read_timeout is not None else timeout,
                "total_timeout": total_timeout if total_timeout is not None else timeout,
                "max_bytes": max_bytes,
                "max_redirects": max_redirects,
            },
            timeout_seconds=float(total_timeout if total_timeout is not None else timeout) + 30.0,
        )
        try:
            body = base64.b64decode(str(result.get("body_b64", "")), validate=True)
        except (ValueError, TypeError) as exc:
            raise SecError(P11Reason.P11_SEC_DISCOVERY_FAILED, "SEC runtime response body is invalid") from exc
        return SecResponse(
            status=int(result.get("status", 0)),
            headers=dict(result.get("headers") or {}),
            body=body,
            final_url=str(result.get("final_url") or url),
        )

    def __call__(self, url: str, headers: dict[str, str], timeout: float) -> SecResponse:
        return self.fetch(url, headers, timeout, max_bytes=512 * 1024 * 1024)


__all__ = ["SEC_RUNTIME_VERSION", "SecRuntimeDescriptor", "SecSubprocessTransport", "run_sec_runner"]
