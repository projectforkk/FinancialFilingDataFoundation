from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from financial_filing_data_foundation.mcp import McpCatalog
from financial_filing_data_foundation.research import (
    EvidenceLedger,
    LEDGER_SCHEMA_VERSION,
    ResearchSpecInput,
    build_research_context,
    freeze_research_spec,
)
from financial_filing_data_foundation.research.cli import (
    COMMANDS,
    MAX_STDIN_BYTES,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
SOURCE_ROOT = REPOSITORY_ROOT / "src"


def _canonical(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ) + "\n"


def _env() -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(SOURCE_ROOT)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def _run_cli(
    args: list[str],
    request: object | bytes | None,
) -> subprocess.CompletedProcess[bytes]:
    if request is None:
        raw = b""
    elif isinstance(request, bytes):
        raw = request
    else:
        raw = json.dumps(
            request,
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
    return subprocess.run(
        [
            sys.executable,
            "-B",
            "-m",
            "financial_filing_data_foundation.research.cli",
            *args,
        ],
        input=raw,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=REPOSITORY_ROOT,
        env=_env(),
        check=False,
    )


def _stdout_json(result: subprocess.CompletedProcess[bytes]) -> dict:
    assert result.stderr == b""
    text = result.stdout.decode("utf-8")
    assert text.count("\n") == 1
    return json.loads(text)


def _stderr_json(result: subprocess.CompletedProcess[bytes]) -> dict:
    assert result.stdout == b""
    text = result.stderr.decode("utf-8")
    assert text.count("\n") == 1
    assert "Traceback" not in text
    assert "usage:" not in text.lower()
    return json.loads(text)


def _assert_error(
    result: subprocess.CompletedProcess[bytes],
    *,
    reason: str,
    exit_code: int,
    command: str | None,
) -> dict:
    assert result.returncode == exit_code
    payload = _stderr_json(result)
    assert payload["status"] == "ERROR"
    assert payload["reason_code"] == reason
    assert payload["command"] == command
    assert set(payload) == {"command", "message", "reason_code", "status"}
    assert result.stderr.decode("utf-8") == _canonical(payload)
    return payload


@pytest.fixture()
def cli_fixture(tmp_path: Path):
    root = tmp_path / "root"
    root.mkdir()
    (root / "inputs").mkdir()
    rules = root / "inputs" / "rules.md"
    rules.write_bytes(b"rules\n")
    (root / "review").mkdir()
    catalog_path = root / "catalog.json"
    catalog_path.write_text(
        json.dumps(
            {
                "schema_version": "p8-mcp-catalog-v1",
                "documents": [],
            },
            separators=(",", ":"),
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )

    bundle = freeze_research_spec(
        root,
        [ResearchSpecInput("rules", "inputs/rules.md")],
    )
    catalog = McpCatalog.load(root, "catalog.json")
    context = build_research_context(bundle, catalog, "review")
    ledger = EvidenceLedger(
        schema_version=LEDGER_SCHEMA_VERSION,
        research_context_id=context.research_context_id,
        spec_bundle_hash=bundle.spec_bundle_hash,
        entries=(),
    )
    return {
        "root": root,
        "rules": rules,
        "catalog_path": catalog_path,
        "bundle": bundle,
        "context": context,
        "ledger": ledger,
    }


def test_exact_four_commands() -> None:
    assert COMMANDS == (
        "freeze-spec",
        "verify-spec",
        "build-context",
        "validate-ledger",
    )


def test_freeze_spec_success(cli_fixture) -> None:
    fx = cli_fixture
    result = _run_cli(
        ["freeze-spec", "--project-root", str(fx["root"])],
        {
            "files": [
                {
                    "logical_name": "rules",
                    "relative_path": "inputs/rules.md",
                }
            ]
        },
    )
    assert result.returncode == 0
    payload = _stdout_json(result)
    assert payload == {
        "command": "freeze-spec",
        "data": fx["bundle"].to_dict(),
        "status": "OK",
    }
    assert result.stdout.decode("utf-8") == _canonical(payload)


def test_verify_spec_success(cli_fixture) -> None:
    fx = cli_fixture
    result = _run_cli(
        ["verify-spec", "--project-root", str(fx["root"])],
        {"spec_bundle": fx["bundle"].to_dict()},
    )
    assert result.returncode == 0
    payload = _stdout_json(result)
    assert payload == {
        "command": "verify-spec",
        "data": {
            "spec_bundle_hash": fx["bundle"].spec_bundle_hash,
            "verified": True,
        },
        "status": "OK",
    }
    assert result.stdout.decode("utf-8") == _canonical(payload)


def test_build_context_success(cli_fixture) -> None:
    fx = cli_fixture
    result = _run_cli(
        [
            "build-context",
            "--project-root",
            str(fx["root"]),
            "--catalog",
            "catalog.json",
            "--p9-review-root",
            "review",
        ],
        {"spec_bundle": fx["bundle"].to_dict()},
    )
    assert result.returncode == 0
    payload = _stdout_json(result)
    assert payload == {
        "command": "build-context",
        "data": fx["context"].to_dict(),
        "status": "OK",
    }
    assert result.stdout.decode("utf-8") == _canonical(payload)


def test_validate_ledger_success(cli_fixture) -> None:
    fx = cli_fixture
    result = _run_cli(
        [
            "validate-ledger",
            "--project-root",
            str(fx["root"]),
            "--catalog",
            "catalog.json",
            "--p9-review-root",
            "review",
        ],
        {
            "spec_bundle": fx["bundle"].to_dict(),
            "ledger": fx["ledger"].to_dict(),
        },
    )
    assert result.returncode == 0
    payload = _stdout_json(result)
    assert payload["command"] == "validate-ledger"
    assert payload["status"] == "OK"
    assert payload["data"]["status"] == "PASS"
    assert payload["data"]["entry_count"] == 0
    assert result.stdout.decode("utf-8") == _canonical(payload)


@pytest.mark.parametrize(
    ("args", "command"),
    [
        ([], None),
        (["unknown"], None),
        (["freeze-spec", "--help"], "freeze-spec"),
        (["freeze-spec"], "freeze-spec"),
        (
            [
                "freeze-spec",
                "--project-root",
                "root",
                "--unknown-option",
                "x",
            ],
            "freeze-spec",
        ),
        (
            [
                "freeze-spec",
                "--project-root",
                "root",
                "--request-file",
                "request.json",
            ],
            "freeze-spec",
        ),
    ],
)
def test_parser_failures_are_json_only(
    args: list[str],
    command: str | None,
) -> None:
    result = _run_cli(args, None)
    _assert_error(
        result,
        reason="P10_CLI_ARGUMENT_ERROR",
        exit_code=2,
        command=command,
    )


@pytest.mark.parametrize(
    "raw_request",
    [
        None,
        b"{",
        b"\xff",
        b"[]",
    ],
)
def test_transport_failures(
    cli_fixture,
    raw_request: bytes | None,
) -> None:
    fx = cli_fixture
    result = _run_cli(
        ["freeze-spec", "--project-root", str(fx["root"])],
        raw_request,
    )
    _assert_error(
        result,
        reason="P10_CLI_INPUT_INVALID",
        exit_code=1,
        command="freeze-spec",
    )


def test_stdin_over_16_mib_rejected(cli_fixture) -> None:
    fx = cli_fixture
    result = _run_cli(
        ["freeze-spec", "--project-root", str(fx["root"])],
        b"{" + (b" " * MAX_STDIN_BYTES),
    )
    _assert_error(
        result,
        reason="P10_CLI_INPUT_INVALID",
        exit_code=1,
        command="freeze-spec",
    )


@pytest.mark.parametrize(
    "payload",
    [
        {"files": [], "extra": 1},
        {},
        {"files": ["not-an-object"]},
        {"files": [{"logical_name": "rules"}]},
    ],
)
def test_freeze_request_shape_rejected(cli_fixture, payload: object) -> None:
    fx = cli_fixture
    result = _run_cli(
        ["freeze-spec", "--project-root", str(fx["root"])],
        payload,
    )
    _assert_error(
        result,
        reason="P10_CLI_INPUT_INVALID",
        exit_code=1,
        command="freeze-spec",
    )


def test_freeze_domain_error_preserved(cli_fixture) -> None:
    fx = cli_fixture
    result = _run_cli(
        ["freeze-spec", "--project-root", str(fx["root"])],
        {
            "files": [
                {
                    "logical_name": " ",
                    "relative_path": "inputs/rules.md",
                }
            ]
        },
    )
    _assert_error(
        result,
        reason="P10_INVALID_SPEC_INPUT",
        exit_code=1,
        command="freeze-spec",
    )


def test_verify_spec_drift_preserved(cli_fixture) -> None:
    fx = cli_fixture
    fx["rules"].write_bytes(b"changed\n")
    result = _run_cli(
        ["verify-spec", "--project-root", str(fx["root"])],
        {"spec_bundle": fx["bundle"].to_dict()},
    )
    _assert_error(
        result,
        reason="P10_RESEARCH_SPEC_CHANGED",
        exit_code=1,
        command="verify-spec",
    )


def test_build_spec_drift_precedes_invalid_catalog(cli_fixture) -> None:
    fx = cli_fixture
    fx["rules"].write_bytes(b"changed\n")
    fx["catalog_path"].write_text("{not-json", encoding="utf-8")
    result = _run_cli(
        [
            "build-context",
            "--project-root",
            str(fx["root"]),
            "--catalog",
            "catalog.json",
            "--p9-review-root",
            "review",
        ],
        {"spec_bundle": fx["bundle"].to_dict()},
    )
    _assert_error(
        result,
        reason="P10_RESEARCH_SPEC_CHANGED",
        exit_code=1,
        command="build-context",
    )


def test_validate_spec_drift_precedes_invalid_ledger(cli_fixture) -> None:
    fx = cli_fixture
    fx["rules"].write_bytes(b"changed\n")
    result = _run_cli(
        [
            "validate-ledger",
            "--project-root",
            str(fx["root"]),
            "--catalog",
            "catalog.json",
            "--p9-review-root",
            "review",
        ],
        {
            "spec_bundle": fx["bundle"].to_dict(),
            "ledger": {"bad": "shape"},
        },
    )
    _assert_error(
        result,
        reason="P10_RESEARCH_SPEC_CHANGED",
        exit_code=1,
        command="validate-ledger",
    )


@pytest.mark.parametrize(
    "catalog",
    [
        "C:catalog.json",
        "../catalog.json",
    ],
)
def test_catalog_escape_forms_rejected(cli_fixture, catalog: str) -> None:
    fx = cli_fixture
    result = _run_cli(
        [
            "build-context",
            "--project-root",
            str(fx["root"]),
            "--catalog",
            catalog,
            "--p9-review-root",
            "review",
        ],
        {"spec_bundle": fx["bundle"].to_dict()},
    )
    _assert_error(
        result,
        reason="P10_CATALOG_INVALID",
        exit_code=1,
        command="build-context",
    )


def test_absolute_catalog_rejected(cli_fixture) -> None:
    fx = cli_fixture
    result = _run_cli(
        [
            "build-context",
            "--project-root",
            str(fx["root"]),
            "--catalog",
            str(fx["catalog_path"].resolve()),
            "--p9-review-root",
            "review",
        ],
        {"spec_bundle": fx["bundle"].to_dict()},
    )
    _assert_error(
        result,
        reason="P10_CATALOG_INVALID",
        exit_code=1,
        command="build-context",
    )


def test_invalid_catalog_maps_to_p10_catalog_invalid(cli_fixture) -> None:
    fx = cli_fixture
    fx["catalog_path"].write_text("{not-json", encoding="utf-8")
    result = _run_cli(
        [
            "build-context",
            "--project-root",
            str(fx["root"]),
            "--catalog",
            "catalog.json",
            "--p9-review-root",
            "review",
        ],
        {"spec_bundle": fx["bundle"].to_dict()},
    )
    _assert_error(
        result,
        reason="P10_CATALOG_INVALID",
        exit_code=1,
        command="build-context",
    )


def test_invalid_review_root_preserves_context_reason(cli_fixture) -> None:
    fx = cli_fixture
    result = _run_cli(
        [
            "build-context",
            "--project-root",
            str(fx["root"]),
            "--catalog",
            "catalog.json",
            "--p9-review-root",
            "missing-review",
        ],
        {"spec_bundle": fx["bundle"].to_dict()},
    )
    _assert_error(
        result,
        reason="P10_CONTEXT_INCOMPATIBLE",
        exit_code=1,
        command="build-context",
    )


def test_malformed_ledger_preserves_provenance_reason(cli_fixture) -> None:
    fx = cli_fixture
    result = _run_cli(
        [
            "validate-ledger",
            "--project-root",
            str(fx["root"]),
            "--catalog",
            "catalog.json",
            "--p9-review-root",
            "review",
        ],
        {
            "spec_bundle": fx["bundle"].to_dict(),
            "ledger": {"bad": "shape"},
        },
    )
    _assert_error(
        result,
        reason="P10_PROVENANCE_INVALID",
        exit_code=1,
        command="validate-ledger",
    )


def test_unexpected_failure_has_fixed_envelope(cli_fixture) -> None:
    fx = cli_fixture
    wrapper = (
        "import sys;"
        "import financial_filing_data_foundation.research.cli as c;"
        "c._run=lambda *a,**k:(_ for _ in ()).throw(RuntimeError('boom'));"
        f"sys.argv=['p10','freeze-spec','--project-root',{str(str(fx['root']))!r}];"
        "raise SystemExit(c.main())"
    )
    raw = json.dumps(
        {
            "files": [
                {
                    "logical_name": "rules",
                    "relative_path": "inputs/rules.md",
                }
            ]
        },
        separators=(",", ":"),
    ).encode("utf-8")
    result = subprocess.run(
        [sys.executable, "-B", "-c", wrapper],
        input=raw,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=REPOSITORY_ROOT,
        env=_env(),
        check=False,
    )
    payload = _assert_error(
        result,
        reason="P10_CLI_FAILED",
        exit_code=1,
        command="freeze-spec",
    )
    assert payload["message"] == "unexpected CLI failure"


def test_exact_candidate_source_binding() -> None:
    import financial_filing_data_foundation.research.cli as cli_module

    assert Path(cli_module.__file__).resolve() == (
        SOURCE_ROOT
        / "financial_filing_data_foundation"
        / "research"
        / "cli.py"
    ).resolve()
