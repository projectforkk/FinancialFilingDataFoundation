from __future__ import annotations

import ast
import json
import subprocess
import sys
from pathlib import Path

import pytest

from financial_filing_data_foundation.acquisition import dayu_runner


def test_protocol_constants_are_pinned() -> None:
    assert dayu_runner.PROTOCOL_VERSION == "ffdf-dayu-acquisition-v1"
    assert (
        dayu_runner.DAYU_PINNED_COMMIT
        == "2115c86d5a9027bb51cbbc8a4d0175080732e4e6"
    )
    assert dayu_runner.EXPECTED_DAYU_VERSION == "0.1.4"
    assert dayu_runner.RUNNER_VERSION == "p2-dayu-runner-v1"


def test_request_json_is_strict_utf8_without_bom(tmp_path: Path) -> None:
    request = tmp_path / "request.json"
    request.write_bytes(
        b"\xef\xbb\xbf"
        + json.dumps(
            {
                "protocol_version": dayu_runner.PROTOCOL_VERSION,
                "operation": "doctor",
                "request_id": "bom",
                "dayu_source_dir": str(tmp_path),
            }
        ).encode("utf-8")
    )

    with pytest.raises(dayu_runner.RunnerError) as exc_info:
        dayu_runner._read_request(request)

    assert exc_info.value.reason_code == "RUNNER_PROTOCOL_INVALID"


def test_atomic_json_writer_has_no_bom(tmp_path: Path) -> None:
    output = tmp_path / "response.json"
    dayu_runner._atomic_write_json(output, {"status": "OK", "value": "中文"})

    payload = output.read_bytes()
    assert not payload.startswith(b"\xef\xbb\xbf")
    assert json.loads(payload.decode("utf-8"))["value"] == "中文"
    assert not output.with_name(output.name + ".tmp").exists()


def test_unsupported_operation_returns_structured_error(tmp_path: Path) -> None:
    request = tmp_path / "request.json"
    response = tmp_path / "response.json"
    request.write_text(
        json.dumps(
            {
                "protocol_version": dayu_runner.PROTOCOL_VERSION,
                "operation": "not-supported",
                "request_id": "req-1",
            }
        ),
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(Path(dayu_runner.__file__).resolve()),
            "--request",
            str(request),
            "--response",
            str(response),
        ],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
        shell=False,
    )

    assert completed.returncode == 1
    payload = json.loads(response.read_text(encoding="utf-8"))
    assert payload["status"] == "ERROR"
    assert payload["reason_code"] == "RUNNER_PROTOCOL_INVALID"
    assert payload["request_id"] == "req-1"


def test_runner_has_no_top_level_dayu_import_or_high_level_workflow_import() -> None:
    source_path = Path(dayu_runner.__file__).resolve()
    tree = ast.parse(source_path.read_text(encoding="utf-8"))

    top_level_imports: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.Import):
            top_level_imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            top_level_imports.append(node.module or "")

    assert not any(name == "dayu" or name.startswith("dayu.") for name in top_level_imports)

    source = source_path.read_text(encoding="utf-8")
    assert "from dayu.fins.pipelines.cn_download_filing_workflow import" not in source
    assert "from dayu.fins.pipelines.cn_download_workflow import" not in source
    assert "from dayu.fins.docling_export import" not in source
    assert "convert_pdf_to_docling_json(" not in source


def test_is_within_rejects_sibling_prefix(tmp_path: Path) -> None:
    root = tmp_path / "dayu"
    root.mkdir()
    sibling = tmp_path / "dayu-other"
    sibling.mkdir()

    assert dayu_runner._is_within(root / "child", root)
    assert not dayu_runner._is_within(sibling, root)
