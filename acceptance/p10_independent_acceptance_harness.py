from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from financial_filing_data_foundation.mcp import McpCatalog
from financial_filing_data_foundation.research import (
    EvidenceLedger,
    LEDGER_SCHEMA_VERSION,
    ResearchSpecInput,
    build_research_context,
    freeze_research_spec,
    validate_evidence_ledger,
    verify_research_spec,
)
from financial_filing_data_foundation.review import (
    P9_VERSION,
    POLICY_VERSION,
    RESOLUTION_SCHEMA_VERSION,
    RESOLVED_VIEW_SCHEMA_VERSION,
)


BASE_MANIFEST_SCHEMA = "p10-acceptance-base-manifest-v1"
FIXTURE_MANIFEST_SCHEMA = "p10-acceptance-fixture-manifest-v1"
REPORT_SCHEMA = "p10-independent-acceptance-harness-v1"

PRODUCTION_CANDIDATE = "d8e7d81b4bb5a4f06cead9eba0e2d09884094676"
INTEGRATION_CANDIDATE = "3a805a8f333ac20770d6aec1c8285d93993d18fc"
INTEGRATION_BLOB_SHA256 = (
    "ef10406c9957f7a68a9af001c913deef0a057e166100a2d852c0c8fcd2c46296"
)
CORE_DESIGN_BASELINE = "f8bffca572a6580c0a1f2babc0cc3b0c9e494204"
P8_LOCK_SHA256 = (
    "8e958b8abcfd9b2de829451ffc253932fa26bb473f73837484b75b1019f092ec"
)
P8_SERVER_VERSION = "p8-local-mcp-v1"
P8_TOOLS = (
    "ffdf_list_documents",
    "ffdf_get_document",
    "ffdf_search_document",
    "ffdf_read_pages",
    "ffdf_list_sections",
    "ffdf_list_tables",
    "ffdf_get_table",
    "ffdf_list_raw_facts",
    "ffdf_get_fact",
    "ffdf_get_evidence",
    "ffdf_get_validation",
)

PERFORMANCE_LIMITS = {
    "freeze_spec_s": 2.0,
    "verify_spec_s": 2.0,
    "build_context_s": 2.0,
    "validate_ledger_s": 5.0,
}


class HarnessFailure(RuntimeError):
    pass


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def require(condition: bool, message: str) -> None:
    if not condition:
        raise HarnessFailure(message)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        canonical_json(value) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def inside(root: Path, candidate: Path) -> bool:
    try:
        candidate.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def validate_source_binding(source_root: Path) -> dict[str, Any]:
    import financial_filing_data_foundation.research as research_package
    import financial_filing_data_foundation.research.cli as cli_module
    import financial_filing_data_foundation.research.context as context_module
    import financial_filing_data_foundation.research.provenance as provenance_module
    import financial_filing_data_foundation.research.spec as spec_module

    expected = (source_root / "src").resolve()
    paths = {
        "research": Path(research_package.__file__).resolve(),
        "spec": Path(spec_module.__file__).resolve(),
        "context": Path(context_module.__file__).resolve(),
        "provenance": Path(provenance_module.__file__).resolve(),
        "cli": Path(cli_module.__file__).resolve(),
    }
    for name, path in paths.items():
        require(
            path.is_relative_to(expected),
            f"{name} imported outside frozen candidate source root: {path}",
        )
    require(importlib.util.find_spec("mcp") is None, "main runtime unexpectedly has mcp SDK")
    return {name: str(path) for name, path in paths.items()}


def validate_manifest(project_root: Path, manifest_path: Path) -> dict[str, Any]:
    manifest = load_json(manifest_path)
    require(
        manifest.get("schema_version") == BASE_MANIFEST_SCHEMA,
        "base manifest schema mismatch",
    )
    checked = 0
    for entry in manifest.get("entries", []):
        path = project_root / entry["path"]
        require(path.is_file(), f"base manifest path missing: {entry['path']}")
        raw = path.read_bytes()
        require(len(raw) == entry["size"], f"base size drift: {entry['path']}")
        require(
            sha256_bytes(raw) == entry["sha256"],
            f"base SHA drift: {entry['path']}",
        )
        checked += 1
    require(checked > 0, "base manifest is empty")
    return {
        "entry_count": checked,
        "manifest_sha256": sha256_bytes(manifest_path.read_bytes()),
    }


def validate_and_copy_fixtures(
    source_root: Path,
    project_root: Path,
    work_root: Path,
) -> dict[str, Any]:
    manifest_git_path = "acceptance/p10-fixtures/manifest.json"
    manifest_raw = run_git(
        source_root,
        "cat-file",
        "blob",
        f"HEAD:{manifest_git_path}",
    )
    try:
        manifest = json.loads(manifest_raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HarnessFailure("fixture manifest Git blob is not valid UTF-8 JSON") from exc
    require(
        manifest.get("schema_version") == FIXTURE_MANIFEST_SCHEMA,
        "fixture manifest schema mismatch",
    )
    inputs = work_root / "inputs"
    inputs.mkdir(parents=True, exist_ok=True)
    copied: dict[str, str] = {}
    for item in manifest.get("fixtures", []):
        name = str(item["name"])
        raw = run_git(
            source_root,
            "cat-file",
            "blob",
            f"HEAD:acceptance/p10-fixtures/{name}",
        )
        require(len(raw) == item["size"], f"fixture size drift: {name}")
        require(
            sha256_bytes(raw) == item["sha256"],
            f"fixture SHA drift: {name}",
        )
        destination = inputs / name
        destination.write_bytes(raw)
        require(destination.read_bytes() == raw, f"fixture copy mismatch: {name}")
        require(inside(project_root, destination), "fixture copy outside project root")
        copied[name] = item["sha256"]
    require(len(copied) == 8, "unexpected fixture count")
    return {
        "fixture_manifest_sha256": sha256_bytes(manifest_raw),
        "fixture_identity_source": "GIT_BLOB",
        "fixtures": copied,
    }


def run_git(source_root: Path, *args: str) -> bytes:
    result = subprocess.run(
        ["git", *args],
        cwd=source_root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    require(
        result.returncode == 0,
        f"git command failed: {' '.join(args)}: {result.stderr.decode(errors='replace')}",
    )
    return result.stdout


def validate_git_freezes(source_root: Path) -> dict[str, Any]:
    blob = run_git(
        source_root,
        "cat-file",
        "blob",
        f"{INTEGRATION_CANDIDATE}:integration/p10/FFDF_RESEARCH_INTEGRATION.md",
    )
    require(
        sha256_bytes(blob) == INTEGRATION_BLOB_SHA256,
        "integration Git blob SHA mismatch",
    )

    source_drift = run_git(
        source_root,
        "diff",
        "--name-only",
        f"{PRODUCTION_CANDIDATE}..HEAD",
        "--",
        "src/financial_filing_data_foundation/research",
        "tests/unit/research",
    ).decode("utf-8")
    require(source_drift.strip() == "", "P10 source/test drift after production candidate")

    integration_drift = run_git(
        source_root,
        "diff",
        "--name-only",
        f"{INTEGRATION_CANDIDATE}..HEAD",
        "--",
        "integration/p10/FFDF_RESEARCH_INTEGRATION.md",
    ).decode("utf-8")
    require(integration_drift.strip() == "", "integration artifact drift")

    design_drift = run_git(
        source_root,
        "diff",
        "--name-only",
        f"{CORE_DESIGN_BASELINE}..HEAD",
        "--",
        "design/24-p10-codex-dynamic-research-integration-design.md",
        "design/25-p10-implementation-plan.md",
        "acceptance/38-p10-acceptance-instruction.md",
    ).decode("utf-8")
    require(design_drift.strip() == "", "core design/acceptance drift")

    return {
        "integration_blob_sha256": sha256_bytes(blob),
        "source_test_drift": [],
        "integration_drift": [],
        "core_design_drift": [],
    }


def validate_security_scope(source_root: Path) -> dict[str, Any]:
    research_root = source_root / "src" / "financial_filing_data_foundation" / "research"
    texts = {
        path.name: path.read_text(encoding="utf-8")
        for path in sorted(research_root.glob("*.py"))
    }
    banned_import_patterns = (
        r"(?m)^\s*(?:from|import)\s+openai\b",
        r"(?m)^\s*(?:from|import)\s+anthropic\b",
        r"(?m)^\s*(?:from|import)\s+requests\b",
        r"(?m)^\s*(?:from|import)\s+httpx\b",
        r"(?m)^\s*(?:from|import)\s+socket\b",
        r"(?m)^\s*(?:from|import)\s+subprocess\b",
        r"(?m)^\s*(?:from|import)\s+sqlite3\b",
        r"(?m)^\s*(?:from|import)\s+sqlalchemy\b",
        r"(?m)^\s*(?:from|import)\s+mcp\b",
    )
    for filename, text in texts.items():
        for pattern in banned_import_patterns:
            require(
                re.search(pattern, text) is None,
                f"forbidden production import in {filename}: {pattern}",
            )
    joined = "\n".join(texts.values())
    for symbol in (
        "prepare_review_overlay",
        "submit_resolution",
        "materialize_resolved_view",
    ):
        require(symbol not in joined, f"P9 mutation API in P10 production: {symbol}")

    for relative in (
        "src/financial_filing_data_foundation/semantic",
        "src/financial_filing_data_foundation/sec",
        "src/financial_filing_data_foundation/research_mcp",
    ):
        require(not (source_root / relative).exists(), f"future production path present: {relative}")

    return {
        "forbidden_production_surface": "NONE",
        "future_production_paths": "ABSENT",
    }


def validate_p8_contract(
    project_root: Path,
    source_root: Path,
    mcp_python: Path,
) -> dict[str, Any]:
    lock_path = project_root / "runtime-locks" / "mcp-2.3.0-py312-win-amd64.lock.txt"
    require(sha256_bytes(lock_path.read_bytes()) == P8_LOCK_SHA256, "P8 runtime lock drift")

    code = (
        "import json;"
        "from financial_filing_data_foundation.mcp.server import TOOL_NAMES,SERVER_VERSION;"
        "print(json.dumps({'server_version':SERVER_VERSION,'tools':list(TOOL_NAMES)},sort_keys=True))"
    )
    env = os.environ.copy()
    env["PYTHONPATH"] = str((source_root / "src").resolve())
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    result = subprocess.run(
        [str(mcp_python), "-B", "-c", code],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        cwd=source_root,
        check=False,
    )
    require(result.returncode == 0, "P8 dedicated runtime contract probe failed")
    data = json.loads(result.stdout.decode("utf-8"))
    require(data["server_version"] == P8_SERVER_VERSION, "P8 server version drift")
    require(tuple(data["tools"]) == P8_TOOLS, "P8 tool list drift")
    return {
        "server_version": data["server_version"],
        "tool_count": len(data["tools"]),
        "tools": data["tools"],
        "runtime_lock_sha256": P8_LOCK_SHA256,
    }


def validate_p9_contract() -> dict[str, str]:
    expected = {
        "p9_version": "p9-review-overlay-v1",
        "policy_version": "p9-review-policy-v1",
        "resolution_schema_version": "p9-review-resolution-v1",
        "resolved_view_schema_version": "p9-resolved-view-v1",
    }
    observed = {
        "p9_version": P9_VERSION,
        "policy_version": POLICY_VERSION,
        "resolution_schema_version": RESOLUTION_SCHEMA_VERSION,
        "resolved_view_schema_version": RESOLVED_VIEW_SCHEMA_VERSION,
    }
    require(observed == expected, "P9 public policy/schema drift")
    return observed


def timed_plumbing(
    project_root: Path,
    work_root: Path,
) -> dict[str, float]:
    catalog = McpCatalog.load(project_root, "workspace/mcp/p8-live-catalog.json")
    review_empty = work_root / "review-empty"
    review_empty.mkdir(parents=True, exist_ok=True)
    spec_path = work_root / "inputs" / "spec-a.md"
    rel = spec_path.resolve().relative_to(project_root.resolve()).as_posix()

    start = time.perf_counter()
    bundle = freeze_research_spec(
        project_root,
        [ResearchSpecInput("runtime_spec", rel)],
    )
    freeze_s = time.perf_counter() - start

    start = time.perf_counter()
    verify_research_spec(project_root, bundle)
    verify_s = time.perf_counter() - start

    review_rel = review_empty.resolve().relative_to(project_root.resolve()).as_posix()
    start = time.perf_counter()
    context = build_research_context(bundle, catalog, review_rel)
    build_s = time.perf_counter() - start

    ledger = EvidenceLedger(
        schema_version=LEDGER_SCHEMA_VERSION,
        research_context_id=context.research_context_id,
        spec_bundle_hash=bundle.spec_bundle_hash,
        entries=(),
    )
    start = time.perf_counter()
    validation = validate_evidence_ledger(context, ledger, bundle, catalog)
    validate_s = time.perf_counter() - start
    require(validation.status == "PASS", "empty performance ledger did not validate")

    observed = {
        "freeze_spec_s": freeze_s,
        "verify_spec_s": verify_s,
        "build_context_s": build_s,
        "validate_ledger_s": validate_s,
    }
    for name, limit in PERFORMANCE_LIMITS.items():
        require(observed[name] <= limit, f"performance gate failed: {name}={observed[name]} > {limit}")
    return observed


def cli_call(
    source_root: Path,
    project_root: Path,
    args: list[str],
    request: bytes,
) -> subprocess.CompletedProcess[bytes]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str((source_root / "src").resolve())
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        [
            sys.executable,
            "-B",
            "-m",
            "financial_filing_data_foundation.research.cli",
            *args,
        ],
        input=request,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=project_root,
        env=env,
        check=False,
    )


def validate_cli_critical(
    source_root: Path,
    project_root: Path,
    work_root: Path,
) -> dict[str, Any]:
    spec_rel = (work_root / "inputs" / "spec-a.md").resolve().relative_to(
        project_root.resolve()
    ).as_posix()
    review_rel = (work_root / "review-empty").resolve().relative_to(
        project_root.resolve()
    ).as_posix()
    freeze_request = canonical_json(
        {"files": [{"logical_name": "runtime_spec", "relative_path": spec_rel}]}
    ).encode("utf-8")
    freeze = cli_call(
        source_root,
        project_root,
        ["freeze-spec", "--project-root", str(project_root)],
        freeze_request,
    )
    require(freeze.returncode == 0 and freeze.stderr == b"", "CLI freeze-spec failed")
    require(freeze.stdout.endswith(b"\n") and b"\r\n" not in freeze.stdout, "CLI output not LF-only")
    freeze_data = json.loads(freeze.stdout)

    verify = cli_call(
        source_root,
        project_root,
        ["verify-spec", "--project-root", str(project_root)],
        canonical_json({"spec_bundle": freeze_data["data"]}).encode("utf-8"),
    )
    require(verify.returncode == 0 and verify.stderr == b"", "CLI verify-spec failed")

    build = cli_call(
        source_root,
        project_root,
        [
            "build-context",
            "--project-root",
            str(project_root),
            "--catalog",
            "workspace/mcp/p8-live-catalog.json",
            "--p9-review-root",
            review_rel,
        ],
        canonical_json({"spec_bundle": freeze_data["data"]}).encode("utf-8"),
    )
    require(build.returncode == 0 and build.stderr == b"", "CLI build-context failed")
    context = json.loads(build.stdout)["data"]

    empty_ledger = {
        "schema_version": LEDGER_SCHEMA_VERSION,
        "research_context_id": context["research_context_id"],
        "spec_bundle_hash": freeze_data["data"]["spec_bundle_hash"],
        "entries": [],
    }
    validate = cli_call(
        source_root,
        project_root,
        [
            "validate-ledger",
            "--project-root",
            str(project_root),
            "--catalog",
            "workspace/mcp/p8-live-catalog.json",
            "--p9-review-root",
            review_rel,
        ],
        canonical_json(
            {"spec_bundle": freeze_data["data"], "ledger": empty_ledger}
        ).encode("utf-8"),
    )
    require(validate.returncode == 0 and validate.stderr == b"", "CLI validate-ledger failed")
    require(json.loads(validate.stdout)["data"]["status"] == "PASS", "CLI ledger result not PASS")

    parser = cli_call(source_root, project_root, ["unknown"], b"")
    require(parser.returncode == 2 and parser.stdout == b"", "CLI parser exit/output mismatch")
    parser_error = json.loads(parser.stderr)
    require(parser_error["reason_code"] == "P10_CLI_ARGUMENT_ERROR", "CLI parser reason mismatch")
    require(b"usage:" not in parser.stderr.lower(), "CLI emitted argparse usage prose")

    malformed = cli_call(
        source_root,
        project_root,
        ["freeze-spec", "--project-root", str(project_root)],
        b"{",
    )
    require(malformed.returncode == 1 and malformed.stdout == b"", "CLI malformed input mismatch")
    malformed_error = json.loads(malformed.stderr)
    require(
        malformed_error["reason_code"] == "P10_CLI_INPUT_INVALID",
        "CLI malformed input reason mismatch",
    )

    return {
        "freeze_spec": "PASS",
        "verify_spec": "PASS",
        "build_context": "PASS",
        "validate_ledger": "PASS",
        "parser_json_error": "PASS",
        "malformed_json_error": "PASS",
        "lf_only": True,
    }


def precheck(
    project_root: Path,
    source_root: Path,
    work_root: Path,
    mcp_python: Path,
) -> dict[str, Any]:
    require(inside(project_root, source_root), "source root outside project root")
    require(inside(project_root, work_root), "work root outside project root")
    require(not work_root.exists(), "acceptance work root must be fresh")
    work_root.mkdir(parents=True)

    source_binding = validate_source_binding(source_root)
    fixtures = validate_and_copy_fixtures(source_root, project_root, work_root)
    base = validate_manifest(
        project_root,
        source_root / "acceptance" / "p10-base-immutability-manifest.json",
    )
    git_freezes = validate_git_freezes(source_root)
    security = validate_security_scope(source_root)
    p8 = validate_p8_contract(project_root, source_root, mcp_python)
    p9 = validate_p9_contract()
    performance = timed_plumbing(project_root, work_root)
    cli = validate_cli_critical(source_root, project_root, work_root)

    return {
        "status": "PASS",
        "phase": "pre",
        "source_binding": source_binding,
        "fixtures": fixtures,
        "base_manifest": base,
        "git_freezes": git_freezes,
        "security": security,
        "p8_contract": p8,
        "p9_contract": p9,
        "performance": performance,
        "cli_critical": cli,
    }


def postcheck(
    project_root: Path,
    source_root: Path,
    work_root: Path,
) -> dict[str, Any]:
    require(work_root.is_dir(), "acceptance work root missing")
    base = validate_manifest(
        project_root,
        source_root / "acceptance" / "p10-base-immutability-manifest.json",
    )
    results = work_root / "results"
    dynamic_a = load_json(results / "dynamic-a.json")
    dynamic_b = load_json(results / "dynamic-b.json")
    live = load_json(results / "live.json")
    negative = load_json(results / "negative.json")

    require(dynamic_a.get("status") == "PASS", "dynamic A not PASS")
    require(dynamic_b.get("status") == "PASS", "dynamic B not PASS")
    require(
        dynamic_a.get("spec_bundle_hash") != dynamic_b.get("spec_bundle_hash"),
        "dynamic spec hashes did not differ",
    )
    require(
        dynamic_a.get("tools_selected") != dynamic_b.get("tools_selected"),
        "dynamic tool selections did not differ",
    )
    require(dynamic_a.get("ledger_validation") == "PASS", "dynamic A ledger invalid")
    require(dynamic_b.get("ledger_validation") == "PASS", "dynamic B ledger invalid")

    require(live.get("run_status") == "COMPLETE", "live run not COMPLETE")
    require(live.get("evidence_ledger_validation") == "PASS", "live ledger invalid")
    require(live.get("raw_numeric_value_changed") is False, "live raw numeric value changed")
    require(live.get("base_validation_status") == "REVIEW_REQUIRED", "live base status mismatch")
    require(
        live.get("review_required_data_usable_for_claim") is True,
        "REVIEW_REQUIRED incorrectly treated as unusable",
    )
    require(live.get("canonical_reuse_eligible") is False, "live canonical reuse incorrectly enabled")
    require(live.get("resolved_reuse_eligible") is False, "live resolved reuse incorrectly enabled")

    expected_negative = {
        "K1": "P10_DATA_PREPARATION_REQUIRED",
        "K2": "P10_VISUAL_CAPABILITY_REQUIRED",
        "K3": "P10_UPSTREAM_INVALID",
        "K4": "P10_RESEARCH_SPEC_CHANGED",
        "K5": "P10_REVIEW_UNRESOLVED",
    }
    for key, reason in expected_negative.items():
        require(negative.get(key) == reason, f"negative {key} mismatch")
    require(negative.get("k1_download_attempted") is False, "K1 downloaded data")
    require(negative.get("k2_guessed_visual") is False, "K2 guessed visual")
    require(negative.get("k3_silent_raw_fallback") is False, "K3 silently fell back")
    require(negative.get("k4_silent_refresh") is False, "K4 silently refreshed spec")
    require(negative.get("k5_guessed_semantic") is False, "K5 guessed semantic value")

    suspicious = []
    for path in work_root.rglob("*"):
        if not path.is_file():
            continue
        lower = path.name.lower()
        if "chain_of_thought" in lower or lower.startswith("reasoning"):
            suspicious.append(path.relative_to(work_root).as_posix())
    require(not suspicious, f"hidden reasoning artifact names present: {suspicious}")

    return {
        "status": "PASS",
        "phase": "post",
        "base_manifest": base,
        "dynamic_spec_hashes_differ": True,
        "dynamic_toolsets_differ": True,
        "live_complete": True,
        "negative_gates": expected_negative,
        "hidden_reasoning_artifacts": [],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=("pre", "post"), required=True)
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--source-root", required=True)
    parser.add_argument("--work-root", required=True)
    parser.add_argument("--mcp-python")
    parser.add_argument("--report", required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    project_root = Path(args.project_root).resolve()
    source_root = Path(args.source_root).resolve()
    work_root = Path(args.work_root).resolve()
    report_path = Path(args.report).resolve()

    require(inside(project_root, report_path), "report path outside project root")

    try:
        if args.phase == "pre":
            require(args.mcp_python is not None, "--mcp-python required for pre phase")
            result = precheck(
                project_root,
                source_root,
                work_root,
                Path(args.mcp_python).resolve(),
            )
        else:
            result = postcheck(project_root, source_root, work_root)
    except Exception as exc:
        result = {
            "schema_version": REPORT_SCHEMA,
            "status": "FAIL",
            "phase": args.phase,
            "error_type": type(exc).__name__,
            "message": str(exc),
        }
        write_json(report_path, result)
        print(canonical_json(result))
        return 1

    result = {"schema_version": REPORT_SCHEMA, **result}
    write_json(report_path, result)
    print(canonical_json(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
