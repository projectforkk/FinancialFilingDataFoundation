from __future__ import annotations

import base64
import json
from pathlib import Path

import pytest

from financial_filing_data_foundation.us_sec.errors import P11Reason, SecError
from financial_filing_data_foundation.us_sec.runtime import (
    SecRuntimeDescriptor,
    SecSubprocessTransport,
    run_sec_runner,
)
from financial_filing_data_foundation.user_cli import _parser


def test_runtime_uses_explicit_argv_without_shell_or_arbitrary_url(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    calls: list[dict[str, object]] = []

    class Completed:
        returncode = 0
        stdout = json.dumps(
            {
                "status": 200,
                "headers": {"Content-Type": "application/json"},
                "body_b64": base64.b64encode(b"{}").decode(),
                "final_url": "https://data.sec.gov/submissions/CIK0000123456.json",
            }
        )
        stderr = ""

    def fake_run(argv: list[str], **kwargs: object) -> Completed:
        calls.append({"argv": argv, **kwargs})
        return Completed()

    monkeypatch.setattr("financial_filing_data_foundation.us_sec.runtime.subprocess.run", fake_run)
    descriptor = SecRuntimeDescriptor.for_project(tmp_path)
    response = run_sec_runner(
        descriptor,
        "fetch",
        {
            "url": "https://data.sec.gov/submissions/CIK0000123456.json",
            "headers": {"User-Agent": "FFDF/Test; contact: ops@example.org"},
            "timeout": 1,
            "max_bytes": 64,
        },
    )
    assert response["status"] == 200
    assert calls[0]["shell"] is False
    assert calls[0]["cwd"] == str(tmp_path.resolve())
    assert "--url" not in calls[0]["argv"]

    with pytest.raises(SecError) as exc_info:
        SecSubprocessTransport(descriptor).validate_url("https://example.com/file")
    assert exc_info.value.reason_code == P11Reason.P11_ARCHIVE_HOST_REJECTED.value


def test_us_cli_accepts_q2_and_explicit_cik_without_ticker() -> None:
    args = _parser().parse_args(
        ["acquire", "--market", "US", "--cik", "320193", "--year", "2025", "--period", "Q2"]
    )
    assert args.cik == "320193"
    assert args.ticker is None
    assert args.period == "Q2"

