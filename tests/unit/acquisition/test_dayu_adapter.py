from __future__ import annotations

import inspect
import json
import subprocess
from pathlib import Path

import pytest

from financial_filing_data_foundation.acquisition import dayu_adapter
from financial_filing_data_foundation.acquisition.dayu_adapter import DayuSubprocessAdapter
from financial_filing_data_foundation.acquisition.dayu_protocol import atomic_write_json
from financial_filing_data_foundation.acquisition.models import (
    AcquisitionError,
    AcquisitionReason,
    DAYU_PACKAGE_VERSION,
    DAYU_PINNED_COMMIT,
    DAYU_REPOSITORY,
    DayuRuntimeDescriptor,
    PROTOCOL_VERSION,
)


def _runtime(tmp_path: Path) -> DayuRuntimeDescriptor:
    source = tmp_path / "dayu-source"
    source.mkdir()
    python = tmp_path / "dayu-python.exe"
    python.write_bytes(b"placeholder")
    return DayuRuntimeDescriptor(
        dayu_repository=DAYU_REPOSITORY,
        dayu_commit=DAYU_PINNED_COMMIT,
        dayu_package_version=DAYU_PACKAGE_VERSION,
        dayu_source_path=source,
        dayu_python_executable=python,
    )


def _runner(tmp_path: Path) -> Path:
    runner = tmp_path / "runner.py"
    runner.write_text("# runner\n", encoding="utf-8")
    return runner


def test_adapter_uses_args_list_shell_false_and_explicit_cwd(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime = _runtime(tmp_path)
    workspace = tmp_path / "neutral-workspace"
    adapter = DayuSubprocessAdapter(
        runtime=runtime,
        runner_script=_runner(tmp_path),
        workspace_root=workspace,
    )
    observed: dict[str, object] = {}

    def fake_run(command, **kwargs):
        observed["command"] = command
        observed["kwargs"] = kwargs
        request_path = Path(command[command.index("--request") + 1])
        response_path = Path(command[command.index("--response") + 1])
        request = json.loads(request_path.read_text(encoding="utf-8"))
        atomic_write_json(
            response_path,
            {
                "protocol_version": PROTOCOL_VERSION,
                "operation": "doctor",
                "request_id": request["request_id"],
                "status": "OK",
            },
        )
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(dayu_adapter.subprocess, "run", fake_run)

    response = adapter.doctor()

    assert response["status"] == "OK"
    command = observed["command"]
    kwargs = observed["kwargs"]
    assert isinstance(command, list)
    assert kwargs["shell"] is False
    assert Path(kwargs["cwd"]).resolve() == workspace.resolve()
    assert kwargs["timeout"] == 60.0
    assert command[0] == str(runtime.dayu_python_executable)
    assert "--request" in command
    assert "--response" in command


def test_adapter_timeout_is_structured(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    adapter = DayuSubprocessAdapter(
        runtime=_runtime(tmp_path),
        runner_script=_runner(tmp_path),
        workspace_root=tmp_path / "workspace",
        doctor_timeout_seconds=3.5,
    )

    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd=args[0], timeout=kwargs["timeout"])

    monkeypatch.setattr(dayu_adapter.subprocess, "run", timeout)

    with pytest.raises(AcquisitionError) as exc_info:
        adapter.doctor()

    assert exc_info.value.reason_code == AcquisitionReason.RUNNER_TIMEOUT.value
    assert exc_info.value.retryable is True


def test_adapter_rejects_mismatched_response_request_id(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    adapter = DayuSubprocessAdapter(
        runtime=_runtime(tmp_path),
        runner_script=_runner(tmp_path),
        workspace_root=tmp_path / "workspace",
    )

    def fake_run(command, **kwargs):
        response_path = Path(command[command.index("--response") + 1])
        atomic_write_json(
            response_path,
            {
                "protocol_version": PROTOCOL_VERSION,
                "request_id": "wrong",
                "status": "OK",
            },
        )
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(dayu_adapter.subprocess, "run", fake_run)

    with pytest.raises(AcquisitionError) as exc_info:
        adapter.doctor()
    assert (
        exc_info.value.reason_code
        == AcquisitionReason.RUNNER_PROTOCOL_INVALID.value
    )


def test_adapter_maps_structured_runner_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    adapter = DayuSubprocessAdapter(
        runtime=_runtime(tmp_path),
        runner_script=_runner(tmp_path),
        workspace_root=tmp_path / "workspace",
    )

    def fake_run(command, **kwargs):
        request_path = Path(command[command.index("--request") + 1])
        response_path = Path(command[command.index("--response") + 1])
        request = json.loads(request_path.read_text(encoding="utf-8"))
        atomic_write_json(
            response_path,
            {
                "protocol_version": PROTOCOL_VERSION,
                "request_id": request["request_id"],
                "status": "ERROR",
                "reason_code": "DISCOVERY_FAILED",
                "retryable": True,
                "message": "upstream unavailable",
            },
        )
        return subprocess.CompletedProcess(command, 1, "", "")

    monkeypatch.setattr(dayu_adapter.subprocess, "run", fake_run)

    with pytest.raises(AcquisitionError) as exc_info:
        adapter.doctor()

    assert exc_info.value.reason_code == "DISCOVERY_FAILED"
    assert exc_info.value.retryable is True


def test_adapter_workspace_must_not_be_inside_dayu_checkout(tmp_path: Path) -> None:
    runtime = _runtime(tmp_path)
    with pytest.raises(ValueError, match="workspace"):
        DayuSubprocessAdapter(
            runtime=runtime,
            runner_script=_runner(tmp_path),
            workspace_root=runtime.dayu_source_path / "workspace",
        )


def test_main_adapter_has_no_direct_dayu_import() -> None:
    source = inspect.getsource(dayu_adapter)
    assert "import dayu" not in source
    assert "from dayu" not in source
