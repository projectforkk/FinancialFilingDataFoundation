from __future__ import annotations

import argparse
import importlib.metadata
import inspect
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Sequence


PROTOCOL_VERSION = "ffdf-dayu-acquisition-v1"
DAYU_REPOSITORY = "https://github.com/noho/dayu-agent"
DAYU_PINNED_COMMIT = "2115c86d5a9027bb51cbbc8a4d0175080732e4e6"
EXPECTED_DAYU_VERSION = "0.1.4"

_REASON_PROTOCOL_INVALID = "RUNNER_PROTOCOL_INVALID"
_REASON_SOURCE_MISMATCH = "DAYU_SOURCE_COMMIT_MISMATCH"
_REASON_SOURCE_DIRTY = "DAYU_WORKTREE_DIRTY"
_REASON_CWD_UNSAFE = "RUNNER_CWD_UNSAFE"
_REASON_RUNTIME_INVALID = "DAYU_RUNTIME_UNAVAILABLE"


class RunnerError(RuntimeError):
    def __init__(self, reason_code: str, message: str) -> None:
        super().__init__(message)
        self.reason_code = reason_code


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path = path.expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _read_request(path: Path) -> dict[str, Any]:
    try:
        raw = json.loads(path.expanduser().resolve().read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RunnerError(_REASON_PROTOCOL_INVALID, f"cannot read request JSON: {exc}") from exc
    if not isinstance(raw, dict):
        raise RunnerError(_REASON_PROTOCOL_INVALID, "request JSON must be an object")
    return raw


def _required_text(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise RunnerError(_REASON_PROTOCOL_INVALID, f"{key} must be a non-empty string")
    return value.strip()


def _git(source_dir: Path, *args: str) -> str:
    try:
        completed = subprocess.run(
            ["git", "-C", str(source_dir), *args],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=15,
            shell=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise RunnerError(_REASON_RUNTIME_INVALID, f"git inspection failed: {exc}") from exc
    if completed.returncode != 0:
        message = (completed.stderr or completed.stdout).strip()
        raise RunnerError(
            _REASON_RUNTIME_INVALID,
            f"git {' '.join(args)} failed with exit {completed.returncode}: {message}",
        )
    return completed.stdout.strip()


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def _site_package_roots() -> tuple[Path, ...]:
    roots: list[Path] = []
    prefix = Path(sys.prefix).resolve()
    for candidate in (
        prefix / "Lib" / "site-packages",
        prefix / "lib" / "site-packages",
    ):
        if candidate.exists():
            roots.append(candidate.resolve())
    return tuple(roots)


def _assert_site_packages_origin(origin: Path, label: str) -> None:
    roots = _site_package_roots()
    if not roots:
        raise RunnerError(_REASON_RUNTIME_INVALID, "no site-packages root found")
    if not any(_is_within(origin, root) for root in roots):
        raise RunnerError(
            _REASON_RUNTIME_INVALID,
            f"{label} origin is outside dedicated runtime site-packages: {origin}",
        )


def _doctor(request: dict[str, Any]) -> dict[str, Any]:
    request_id = _required_text(request, "request_id")
    source_dir = Path(_required_text(request, "dayu_source_dir")).expanduser().resolve()

    if request.get("protocol_version") != PROTOCOL_VERSION:
        raise RunnerError(
            _REASON_PROTOCOL_INVALID,
            f"unsupported protocol_version={request.get('protocol_version')!r}",
        )
    if request.get("operation") != "doctor":
        raise RunnerError(
            _REASON_PROTOCOL_INVALID,
            f"doctor runner received operation={request.get('operation')!r}",
        )
    if not source_dir.is_dir():
        raise RunnerError(_REASON_RUNTIME_INVALID, f"Dayu source dir not found: {source_dir}")

    cwd = Path.cwd().resolve()
    if _is_within(cwd, source_dir):
        raise RunnerError(
            _REASON_CWD_UNSAFE,
            f"runner cwd must not be inside Dayu source checkout: {cwd}",
        )

    source_head = _git(source_dir, "rev-parse", "HEAD")
    if source_head != DAYU_PINNED_COMMIT:
        raise RunnerError(
            _REASON_SOURCE_MISMATCH,
            f"expected Dayu commit {DAYU_PINNED_COMMIT}, got {source_head}",
        )

    dirty = _git(source_dir, "status", "--porcelain")
    if dirty:
        raise RunnerError(_REASON_SOURCE_DIRTY, "Dayu source checkout is dirty")

    import_start = time.perf_counter()
    import dayu

    from dayu.fins.downloaders.cninfo_downloader import CninfoDiscoveryClient
    from dayu.fins.downloaders.hkexnews_downloader import HkexnewsDiscoveryClient
    from dayu.fins.pipelines.cn_download_models import CnReportQuery

    import_ms = round((time.perf_counter() - import_start) * 1000.0, 3)

    dayu_version = importlib.metadata.version("dayu-agent")
    if dayu_version != EXPECTED_DAYU_VERSION:
        raise RunnerError(
            _REASON_RUNTIME_INVALID,
            f"expected dayu-agent {EXPECTED_DAYU_VERSION}, got {dayu_version}",
        )

    dayu_origin = Path(dayu.__file__).resolve()
    cn_origin = Path(inspect.getfile(CninfoDiscoveryClient)).resolve()
    hk_origin = Path(inspect.getfile(HkexnewsDiscoveryClient)).resolve()
    query_origin = Path(inspect.getfile(CnReportQuery)).resolve()

    for label, origin in (
        ("dayu", dayu_origin),
        ("CninfoDiscoveryClient", cn_origin),
        ("HkexnewsDiscoveryClient", hk_origin),
        ("CnReportQuery", query_origin),
    ):
        _assert_site_packages_origin(origin, label)

    forbidden_workflow_modules = (
        "dayu.fins.pipelines.cn_download_filing_workflow",
        "dayu.fins.pipelines.cn_download_workflow",
        "dayu.fins.docling_export",
    )
    transitively_loaded_modules = [
        module_name
        for module_name in forbidden_workflow_modules
        if module_name in sys.modules
    ]

    return {
        "protocol_version": PROTOCOL_VERSION,
        "operation": "doctor",
        "request_id": request_id,
        "status": "OK",
        "dayu_repository": DAYU_REPOSITORY,
        "dayu_pinned_commit": DAYU_PINNED_COMMIT,
        "dayu_source_head": source_head,
        "dayu_source_clean": True,
        "dayu_source_dir": str(source_dir),
        "dayu_package_version": dayu_version,
        "python_executable": sys.executable,
        "python_version": sys.version.split()[0],
        "python_build": sys.version.replace("\n", " "),
        "python_prefix": sys.prefix,
        "cwd": str(cwd),
        "site_packages": [str(path) for path in _site_package_roots()],
        "dayu_module_origin": str(dayu_origin),
        "cn_downloader_origin": str(cn_origin),
        "hk_downloader_origin": str(hk_origin),
        "query_model_origin": str(query_origin),
        "import_ms": import_ms,
        "transitively_loaded_modules": transitively_loaded_modules,
        "docling_conversion_used": False,
        "network_used": False,
    }


def _error_payload(request_path: Path, exc: Exception) -> dict[str, Any]:
    request_id: str | None = None
    try:
        raw = json.loads(request_path.read_text(encoding="utf-8"))
        value = raw.get("request_id") if isinstance(raw, dict) else None
        if isinstance(value, str):
            request_id = value
    except Exception:
        pass

    reason_code = exc.reason_code if isinstance(exc, RunnerError) else _REASON_RUNTIME_INVALID
    return {
        "protocol_version": PROTOCOL_VERSION,
        "status": "ERROR",
        "request_id": request_id,
        "reason_code": reason_code,
        "retryable": False,
        "message": str(exc),
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="FFDF P2 narrow Dayu acquisition runner")
    parser.add_argument("--request", required=True, type=Path)
    parser.add_argument("--response", required=True, type=Path)
    args = parser.parse_args(argv)

    request_path = args.request.expanduser().resolve()
    response_path = args.response.expanduser().resolve()

    try:
        request = _read_request(request_path)
        operation = request.get("operation")
        if operation == "doctor":
            response = _doctor(request)
        else:
            raise RunnerError(
                _REASON_PROTOCOL_INVALID,
                f"unsupported operation={operation!r}; P2-E currently enables doctor only",
            )
        _atomic_write_json(response_path, response)
        return 0
    except Exception as exc:
        try:
            _atomic_write_json(response_path, _error_payload(request_path, exc))
        except Exception:
            pass
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
