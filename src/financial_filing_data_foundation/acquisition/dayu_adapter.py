from __future__ import annotations

import subprocess
import uuid
from pathlib import Path
from typing import Any

from financial_filing_data_foundation.acquisition.dayu_protocol import (
    atomic_write_json,
    candidate_to_dict,
    discovery_from_response,
    downloaded_asset_from_response,
    read_json_object,
)
from financial_filing_data_foundation.acquisition.models import (
    AcquisitionCandidate,
    AcquisitionError,
    AcquisitionReason,
    AcquisitionRequest,
    DAYU_PINNED_COMMIT,
    DAYU_PACKAGE_VERSION,
    DAYU_REPOSITORY,
    DayuRuntimeDescriptor,
    DiscoveryResult,
    PROTOCOL_VERSION,
    RunnerDownloadedAsset,
)
from financial_filing_data_foundation.identity import SourceMetadata


class DayuSubprocessAdapter:
    name = "dayu"

    def __init__(
        self,
        *,
        runtime: DayuRuntimeDescriptor,
        runner_script: str | Path,
        workspace_root: str | Path,
        doctor_timeout_seconds: float = 60.0,
        operation_timeout_seconds: float = 120.0,
    ) -> None:
        self.runtime = runtime
        self.runner_script = Path(runner_script).expanduser().resolve()
        self.workspace_root = Path(workspace_root).expanduser().resolve()
        self.doctor_timeout_seconds = doctor_timeout_seconds
        self.operation_timeout_seconds = operation_timeout_seconds

        if runtime.dayu_repository != DAYU_REPOSITORY:
            raise ValueError("Dayu repository descriptor does not match P2 pin")
        if runtime.dayu_commit != DAYU_PINNED_COMMIT:
            raise ValueError("Dayu commit descriptor does not match P2 pin")
        if runtime.dayu_package_version != DAYU_PACKAGE_VERSION:
            raise ValueError("Dayu package descriptor does not match P2 pin")
        if not self.runner_script.is_file():
            raise FileNotFoundError(self.runner_script)

        self.workspace_root.mkdir(parents=True, exist_ok=True)
        if self._is_within(self.workspace_root, runtime.dayu_source_path):
            raise ValueError("adapter workspace must not be inside Dayu source checkout")

    @staticmethod
    def _is_within(path: Path, root: Path) -> bool:
        try:
            path.resolve().relative_to(root.resolve())
        except ValueError:
            return False
        return True

    def _new_protocol_paths(self, request_id: str) -> tuple[Path, Path]:
        protocol_dir = self.workspace_root / "protocol"
        protocol_dir.mkdir(parents=True, exist_ok=True)
        token = uuid.uuid4().hex
        request_path = protocol_dir / f"{request_id}-{token}.request.json"
        response_path = protocol_dir / f"{request_id}-{token}.response.json"
        return request_path, response_path

    def _run(
        self,
        payload: dict[str, Any],
        *,
        timeout_seconds: float,
    ) -> dict[str, Any]:
        request_id = str(payload["request_id"])
        request_path, response_path = self._new_protocol_paths(request_id)
        atomic_write_json(request_path, payload)

        command = [
            str(self.runtime.dayu_python_executable),
            str(self.runner_script),
            "--request",
            str(request_path),
            "--response",
            str(response_path),
        ]
        try:
            completed = subprocess.run(
                command,
                cwd=self.workspace_root,
                shell=False,
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout_seconds,
            )
        except subprocess.TimeoutExpired as exc:
            raise AcquisitionError(
                AcquisitionReason.RUNNER_TIMEOUT,
                f"Dayu runner timed out after {timeout_seconds}s",
                retryable=True,
            ) from exc
        except OSError as exc:
            raise AcquisitionError(
                AcquisitionReason.DAYU_RUNTIME_UNAVAILABLE,
                f"cannot execute Dayu runtime: {exc}",
            ) from exc

        if not response_path.is_file():
            diagnostic = (completed.stderr or completed.stdout).strip()
            raise AcquisitionError(
                AcquisitionReason.RUNNER_PROTOCOL_INVALID,
                "runner produced no response JSON"
                + (f": {diagnostic}" if diagnostic else ""),
            )

        try:
            response = read_json_object(response_path)
        except Exception as exc:
            raise AcquisitionError(
                AcquisitionReason.RUNNER_PROTOCOL_INVALID,
                f"cannot parse runner response: {exc}",
            ) from exc

        if response.get("protocol_version") != PROTOCOL_VERSION:
            raise AcquisitionError(
                AcquisitionReason.RUNNER_PROTOCOL_INVALID,
                "runner response protocol version mismatch",
            )
        if response.get("request_id") != request_id:
            raise AcquisitionError(
                AcquisitionReason.RUNNER_PROTOCOL_INVALID,
                "runner response request_id mismatch",
            )

        if response.get("status") != "OK":
            reason = str(
                response.get("reason_code")
                or AcquisitionReason.RUNNER_PROTOCOL_INVALID.value
            )
            message = str(response.get("message") or "Dayu runner failed")
            retryable = bool(response.get("retryable", False))
            raise AcquisitionError(reason, message, retryable=retryable)

        if completed.returncode != 0:
            raise AcquisitionError(
                AcquisitionReason.RUNNER_PROTOCOL_INVALID,
                f"runner exit={completed.returncode} but response status=OK",
            )
        return response

    def doctor(self) -> dict[str, Any]:
        request_id = f"doctor-{uuid.uuid4().hex}"
        payload = {
            "protocol_version": PROTOCOL_VERSION,
            "operation": "doctor",
            "request_id": request_id,
            "dayu_source_dir": str(self.runtime.dayu_source_path),
        }
        return self._run(payload, timeout_seconds=self.doctor_timeout_seconds)

    def discover_documents(self, request: AcquisitionRequest) -> DiscoveryResult:
        request_id = f"discover-{uuid.uuid4().hex}"
        payload = {
            "protocol_version": PROTOCOL_VERSION,
            "operation": "discover",
            "request_id": request_id,
            "dayu_source_dir": str(self.runtime.dayu_source_path),
            "market": request.slot.market,
            "ticker": request.company.ticker,
            "window_start": request.window_start,
            "window_end": request.window_end,
            "target_periods": [request.slot.raw_fiscal_period],
        }
        response = self._run(
            payload,
            timeout_seconds=self.operation_timeout_seconds,
        )
        try:
            return discovery_from_response(response)
        except Exception as exc:
            raise AcquisitionError(
                AcquisitionReason.RUNNER_PROTOCOL_INVALID,
                f"invalid discovery response: {exc}",
            ) from exc

    def download_document(
        self,
        candidate: AcquisitionCandidate,
        staging_path: Path,
    ) -> RunnerDownloadedAsset:
        request_id = f"download-{uuid.uuid4().hex}"
        payload = {
            "protocol_version": PROTOCOL_VERSION,
            "operation": "download",
            "request_id": request_id,
            "dayu_source_dir": str(self.runtime.dayu_source_path),
            "candidate": candidate_to_dict(candidate),
            "staging_path": str(staging_path.resolve()),
        }
        response = self._run(
            payload,
            timeout_seconds=self.operation_timeout_seconds,
        )
        try:
            return downloaded_asset_from_response(response)
        except Exception as exc:
            raise AcquisitionError(
                AcquisitionReason.RUNNER_PROTOCOL_INVALID,
                f"invalid download response: {exc}",
            ) from exc

    def source_metadata(
        self,
        candidate: AcquisitionCandidate,
        downloaded_at: str,
    ) -> SourceMetadata:
        return SourceMetadata(
            provider=candidate.provider,
            source_id=candidate.source_id,
            source_url=candidate.source_url,
            source_title=candidate.source_title,
            filing_date=candidate.filing_date,
            report_date=None,
            provider_company_id=candidate.provider_company_id,
            acquired_at=downloaded_at,
        )
