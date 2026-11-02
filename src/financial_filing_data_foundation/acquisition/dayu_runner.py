from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import inspect
import json
import os
import shutil
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
_REASON_DISCOVERY_FAILED = "DISCOVERY_FAILED"
_REASON_DOWNLOAD_FAILED = "DOWNLOAD_FAILED"
_REASON_STAGING_WRITE_FAILED = "STAGING_WRITE_FAILED"
_REASON_PDF_VALIDATION_FAILED = "PDF_VALIDATION_FAILED"
_REASON_SHA_MISMATCH = "SHA_MISMATCH"


class RunnerError(RuntimeError):
    def __init__(
        self,
        reason_code: str,
        message: str,
        *,
        retryable: bool = False,
    ) -> None:
        super().__init__(message)
        self.reason_code = reason_code
        self.retryable = retryable


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
        raise RunnerError(
            _REASON_PROTOCOL_INVALID,
            f"cannot read request JSON: {exc}",
        ) from exc
    if not isinstance(raw, dict):
        raise RunnerError(_REASON_PROTOCOL_INVALID, "request JSON must be an object")
    return raw


def _required_text(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise RunnerError(
            _REASON_PROTOCOL_INVALID,
            f"{key} must be a non-empty string",
        )
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
        raise RunnerError(
            _REASON_RUNTIME_INVALID,
            f"git inspection failed: {exc}",
        ) from exc
    if completed.returncode != 0:
        message = (completed.stderr or completed.stdout).strip()
        raise RunnerError(
            _REASON_RUNTIME_INVALID,
            f"git {' '.join(args)} failed with exit "
            f"{completed.returncode}: {message}",
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
            resolved = candidate.resolve()
            if resolved not in roots:
                roots.append(resolved)
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


def _validate_runtime_request(request: dict[str, Any]) -> tuple[str, Path, Path, str]:
    request_id = _required_text(request, "request_id")
    if request.get("protocol_version") != PROTOCOL_VERSION:
        raise RunnerError(
            _REASON_PROTOCOL_INVALID,
            f"unsupported protocol_version={request.get('protocol_version')!r}",
        )

    source_dir = Path(
        _required_text(request, "dayu_source_dir")
    ).expanduser().resolve()
    if not source_dir.is_dir():
        raise RunnerError(
            _REASON_RUNTIME_INVALID,
            f"Dayu source dir not found: {source_dir}",
        )

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

    dayu_version = importlib.metadata.version("dayu-agent")
    if dayu_version != EXPECTED_DAYU_VERSION:
        raise RunnerError(
            _REASON_RUNTIME_INVALID,
            f"expected dayu-agent {EXPECTED_DAYU_VERSION}, got {dayu_version}",
        )

    return request_id, source_dir, cwd, source_head


def _dayu_symbols() -> dict[str, Any]:
    import dayu

    from dayu.fins.downloaders.cninfo_downloader import CninfoDiscoveryClient
    from dayu.fins.downloaders.hkexnews_downloader import HkexnewsDiscoveryClient
    from dayu.fins.pipelines.cn_download_models import (
        CnReportCandidate,
        CnReportQuery,
    )

    origins = {
        "dayu": Path(dayu.__file__).resolve(),
        "CninfoDiscoveryClient": Path(inspect.getfile(CninfoDiscoveryClient)).resolve(),
        "HkexnewsDiscoveryClient": Path(
            inspect.getfile(HkexnewsDiscoveryClient)
        ).resolve(),
        "CnReportQuery": Path(inspect.getfile(CnReportQuery)).resolve(),
        "CnReportCandidate": Path(inspect.getfile(CnReportCandidate)).resolve(),
    }
    for label, origin in origins.items():
        _assert_site_packages_origin(origin, label)

    return {
        "dayu": dayu,
        "CninfoDiscoveryClient": CninfoDiscoveryClient,
        "HkexnewsDiscoveryClient": HkexnewsDiscoveryClient,
        "CnReportQuery": CnReportQuery,
        "CnReportCandidate": CnReportCandidate,
        "origins": origins,
    }


def _doctor(request: dict[str, Any]) -> dict[str, Any]:
    if request.get("operation") != "doctor":
        raise RunnerError(
            _REASON_PROTOCOL_INVALID,
            f"doctor runner received operation={request.get('operation')!r}",
        )

    request_id, source_dir, cwd, source_head = _validate_runtime_request(request)
    import_start = time.perf_counter()
    symbols = _dayu_symbols()
    import_ms = round((time.perf_counter() - import_start) * 1000.0, 3)

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
    origins = symbols["origins"]

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
        "dayu_package_version": EXPECTED_DAYU_VERSION,
        "python_executable": sys.executable,
        "python_version": sys.version.split()[0],
        "python_build": sys.version.replace("\n", " "),
        "python_prefix": sys.prefix,
        "cwd": str(cwd),
        "site_packages": [str(path) for path in _site_package_roots()],
        "dayu_module_origin": str(origins["dayu"]),
        "cn_downloader_origin": str(origins["CninfoDiscoveryClient"]),
        "hk_downloader_origin": str(origins["HkexnewsDiscoveryClient"]),
        "query_model_origin": str(origins["CnReportQuery"]),
        "import_ms": import_ms,
        "transitively_loaded_modules": transitively_loaded_modules,
        "docling_conversion_used": False,
        "network_used": False,
    }


def _client_for_market(market: str, symbols: dict[str, Any]) -> Any:
    if market == "CN":
        return symbols["CninfoDiscoveryClient"]()
    if market == "HK":
        return symbols["HkexnewsDiscoveryClient"]()
    raise RunnerError(
        _REASON_PROTOCOL_INVALID,
        f"unsupported P2 market: {market!r}",
    )


def _candidate_to_wire(profile: Any, candidate: Any) -> dict[str, Any]:
    return {
        "provider": str(candidate.provider),
        "provider_company_id": str(profile.company_id),
        "provider_company_name": str(profile.company_name),
        "ticker": str(profile.ticker),
        "source_id": str(candidate.source_id),
        "source_url": str(candidate.source_url),
        "source_title": str(candidate.title),
        "language": str(candidate.language),
        "filing_date": str(candidate.filing_date),
        "fiscal_year": int(candidate.fiscal_year),
        "fiscal_period": str(candidate.fiscal_period),
        "amended": bool(candidate.amended),
        "remote_content_length": (
            None if candidate.content_length is None else int(candidate.content_length)
        ),
        "etag": None if candidate.etag is None else str(candidate.etag),
        "last_modified": (
            None
            if candidate.last_modified is None
            else str(candidate.last_modified)
        ),
    }


def _discover(request: dict[str, Any]) -> dict[str, Any]:
    if request.get("operation") != "discover":
        raise RunnerError(
            _REASON_PROTOCOL_INVALID,
            f"discover runner received operation={request.get('operation')!r}",
        )
    request_id, _, _, _ = _validate_runtime_request(request)

    market = _required_text(request, "market").upper()
    ticker = _required_text(request, "ticker")
    window_start = _required_text(request, "window_start")
    window_end = _required_text(request, "window_end")
    periods = request.get("target_periods")
    if (
        not isinstance(periods, list)
        or not periods
        or not all(isinstance(item, str) and item.strip() for item in periods)
    ):
        raise RunnerError(
            _REASON_PROTOCOL_INVALID,
            "target_periods must be a non-empty string list",
        )
    normalized_periods = tuple(str(item).strip().upper() for item in periods)

    symbols = _dayu_symbols()
    query = symbols["CnReportQuery"](
        market=market,
        normalized_ticker=ticker,
        start_date=window_start,
        end_date=window_end,
        target_periods=normalized_periods,
    )
    client = _client_for_market(market, symbols)

    try:
        profile = client.resolve_company(query)
        candidates = client.list_report_candidates(query, profile)
    except Exception as exc:
        raise RunnerError(
            _REASON_DISCOVERY_FAILED,
            f"{market} discovery failed: {type(exc).__name__}: {exc}",
            retryable=True,
        ) from exc

    return {
        "protocol_version": PROTOCOL_VERSION,
        "operation": "discover",
        "request_id": request_id,
        "status": "OK",
        "profile": {
            "provider": str(profile.provider),
            "company_id": str(profile.company_id),
            "company_name": str(profile.company_name),
            "ticker": str(profile.ticker),
        },
        "candidates": [
            _candidate_to_wire(profile, candidate) for candidate in candidates
        ],
        "docling_conversion_used": False,
    }


def _candidate_from_wire(payload: dict[str, Any], symbols: dict[str, Any]) -> Any:
    required = (
        "provider",
        "source_id",
        "source_url",
        "source_title",
        "language",
        "filing_date",
        "fiscal_year",
        "fiscal_period",
        "amended",
    )
    missing = [key for key in required if key not in payload]
    if missing:
        raise RunnerError(
            _REASON_PROTOCOL_INVALID,
            "candidate missing fields: " + ", ".join(sorted(missing)),
        )

    return symbols["CnReportCandidate"](
        provider=str(payload["provider"]),
        source_id=str(payload["source_id"]),
        source_url=str(payload["source_url"]),
        title=str(payload["source_title"]),
        language=str(payload["language"]),
        filing_date=str(payload["filing_date"]),
        fiscal_year=int(payload["fiscal_year"]),
        fiscal_period=str(payload["fiscal_period"]),
        amended=bool(payload["amended"]),
        content_length=(
            None
            if payload.get("remote_content_length") is None
            else int(payload["remote_content_length"])
        ),
        etag=None if payload.get("etag") is None else str(payload["etag"]),
        last_modified=(
            None
            if payload.get("last_modified") is None
            else str(payload["last_modified"])
        ),
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _core_candidate_equal(dayu_candidate: Any, wire: dict[str, Any]) -> bool:
    return (
        str(dayu_candidate.provider) == str(wire["provider"])
        and str(dayu_candidate.source_id) == str(wire["source_id"])
        and str(dayu_candidate.source_url) == str(wire["source_url"])
        and str(dayu_candidate.title) == str(wire["source_title"])
        and str(dayu_candidate.language) == str(wire["language"])
        and str(dayu_candidate.filing_date) == str(wire["filing_date"])
        and int(dayu_candidate.fiscal_year) == int(wire["fiscal_year"])
        and str(dayu_candidate.fiscal_period) == str(wire["fiscal_period"])
        and bool(dayu_candidate.amended) == bool(wire["amended"])
    )


def _download(request: dict[str, Any]) -> dict[str, Any]:
    if request.get("operation") != "download":
        raise RunnerError(
            _REASON_PROTOCOL_INVALID,
            f"download runner received operation={request.get('operation')!r}",
        )
    request_id, _, _, _ = _validate_runtime_request(request)

    candidate_payload = request.get("candidate")
    if not isinstance(candidate_payload, dict):
        raise RunnerError(
            _REASON_PROTOCOL_INVALID,
            "candidate must be an object",
        )
    staging_path = Path(
        _required_text(request, "staging_path")
    ).expanduser().resolve()
    if not staging_path.parent.is_dir():
        raise RunnerError(
            _REASON_STAGING_WRITE_FAILED,
            f"staging parent does not exist: {staging_path.parent}",
        )

    symbols = _dayu_symbols()
    candidate = _candidate_from_wire(candidate_payload, symbols)
    provider = str(candidate.provider)
    market = "CN" if provider == "cninfo" else "HK" if provider == "hkexnews" else None
    if market is None:
        raise RunnerError(
            _REASON_PROTOCOL_INVALID,
            f"unsupported provider: {provider!r}",
        )
    client = _client_for_market(market, symbols)

    asset = None
    temp_path: Path | None = None
    try:
        asset = client.download_report_pdf(candidate)
        if not _core_candidate_equal(asset.candidate, candidate_payload):
            raise RunnerError(
                _REASON_PROTOCOL_INVALID,
                "Dayu download result candidate differs from request candidate",
            )
        temp_path = Path(asset.pdf_path).expanduser().resolve()
        if not temp_path.is_file():
            raise RunnerError(
                _REASON_DOWNLOAD_FAILED,
                f"Dayu downloaded PDF is missing: {temp_path}",
            )

        with temp_path.open("rb") as handle:
            if handle.read(5) != b"%PDF-":
                raise RunnerError(
                    _REASON_PDF_VALIDATION_FAILED,
                    "Dayu downloaded object does not start with PDF magic",
                )

        tmp_target = staging_path.with_name(staging_path.name + ".runner.tmp")
        shutil.copyfile(temp_path, tmp_target)
        copied_sha = _sha256(tmp_target)
        copied_size = tmp_target.stat().st_size
        if copied_sha.lower() != str(asset.sha256).lower():
            tmp_target.unlink(missing_ok=True)
            raise RunnerError(
                _REASON_SHA_MISMATCH,
                f"runner copied SHA {copied_sha} != Dayu SHA {asset.sha256}",
            )
        if copied_size != int(asset.content_length):
            tmp_target.unlink(missing_ok=True)
            raise RunnerError(
                _REASON_SHA_MISMATCH,
                f"runner copied size {copied_size} != "
                f"Dayu size {asset.content_length}",
            )

        os.replace(tmp_target, staging_path)
        return {
            "protocol_version": PROTOCOL_VERSION,
            "operation": "download",
            "request_id": request_id,
            "status": "OK",
            "candidate": candidate_payload,
            "dayu_temp_sha256": str(asset.sha256).lower(),
            "dayu_content_length": int(asset.content_length),
            "downloaded_at": str(asset.downloaded_at),
            "staging_path": str(staging_path),
            "docling_conversion_used": False,
        }
    except RunnerError:
        raise
    except Exception as exc:
        raise RunnerError(
            _REASON_DOWNLOAD_FAILED,
            f"{provider} download failed: {type(exc).__name__}: {exc}",
            retryable=True,
        ) from exc
    finally:
        if temp_path is not None and temp_path != staging_path:
            try:
                temp_path.unlink(missing_ok=True)
            except OSError:
                pass


def _error_payload(request_path: Path, exc: Exception) -> dict[str, Any]:
    request_id: str | None = None
    try:
        raw = json.loads(request_path.read_text(encoding="utf-8"))
        value = raw.get("request_id") if isinstance(raw, dict) else None
        if isinstance(value, str):
            request_id = value
    except Exception:
        pass

    if isinstance(exc, RunnerError):
        reason_code = exc.reason_code
        retryable = exc.retryable
    else:
        reason_code = _REASON_RUNTIME_INVALID
        retryable = False
    return {
        "protocol_version": PROTOCOL_VERSION,
        "status": "ERROR",
        "request_id": request_id,
        "reason_code": reason_code,
        "retryable": retryable,
        "message": str(exc),
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="FFDF P2 narrow Dayu acquisition runner"
    )
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
        elif operation == "discover":
            response = _discover(request)
        elif operation == "download":
            response = _download(request)
        else:
            raise RunnerError(
                _REASON_PROTOCOL_INVALID,
                f"unsupported operation={operation!r}",
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
