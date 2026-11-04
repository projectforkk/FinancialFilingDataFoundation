from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from financial_filing_data_foundation.review.evidence import (
    validate_resolution_payload_security,
)
from financial_filing_data_foundation.review.models import (
    ResolutionSubmission,
    ReviewError,
)
from financial_filing_data_foundation.review.queue import (
    list_review_tasks,
    prepare_review_overlay,
)
from financial_filing_data_foundation.review.resolve import (
    load_resolved_snapshot,
    materialize_resolved_view,
)
from financial_filing_data_foundation.review.store import (
    list_resolutions,
    submit_resolution,
)

CATALOG_SHA256 = "e493f2f6a951007c1e5ac932268796d35d33386760f4503d48ff0a7f7a148cdc"
CN_SHA = "5299f4940e2ce4e91084b73dc457d558b9d335fa76fbfee6227e4254eb7f4a30"
HK_SHA = "70f529984a87ef7f46d9e1db26bb9ef27eef9c01d29c59aabf69e557b479a6a0"

CN_QUEUE_SHA = "3fdc6db4fddd3db0620c0aa2db5fdb43f801a00d564a951c3cde61e3f474bd05"
HK_QUEUE_SHA = "c3f427b1148851e00e06d48d11717f917af69695dbd37f2267daa151659989c5"

CN_TASK_ID = "59ebac57b61f85d922a66424fa3468e81fdb0773c0bd25c6c350085058b555a2"
CN_ISSUE_ID = "0a42571e7fd35f3c55f0b7989577d963a6ab39c304e75f4a5e2468c2019662a3"
CN_FACT_ID = "9b3e2e441e6730c0f3c979816dd764dcb4bf70e6cde16caae9e3897733b9a015"
CN_TABLE_ID = "9d9d4afeb104cbcfade4847423919c7b9c60be2efef1011bb4651beb11268075"
CN_CELL_ID = "b44ef475c0de0c3e7241c7990992d63f269254a841fcf93987236d29ca81b046"
CN_RESOLUTION_ID = "8eece78fbfd7ea8917d0410b8255f0c196d8b7ed29df90b4baad1b19c592f5e9"
CN_RESOLUTION_SHA = "ea8bf0096a9233b0e7f973671cc93726af05dd99d12e479eb3178694820cb3fd"
CN_OVERLAY_HASH = "2f7f092a9c91091586704dfe5c1c042055ccf00fe6cf20e80600b87ffa41ea80"
CN_FACTS_SHA = "9f2a104241b5acf8ea8e1ad44905e8b94931a604cf915607f4d4b162a86214d0"
CN_ISSUES_SHA = "221928af579380f3dc47684edc1e55470bd546edffc84bf175bb3e394a6c143b"
CN_REPORT_SHA = "f9659d7ded671b817c8b712e3bc46719ccc5fea536286181825b5e95e5538778"
CN_SNAPSHOT_SHA = "d1a8f92ce5ec9c57b657c60abd1fc1010f6d67cc7a6b30d8d7f3eb722b68c505"

HK_REASONS = {
    "CORE_STATEMENT_COVERAGE_LOW",
    "RAW_PERIOD_COVERAGE_LOW",
    "RAW_UNIT_AMBIGUOUS",
    "RAW_UNIT_COVERAGE_LOW",
}
HK_OVERLAY_HASH = "ecd91784868125f55c65e43cb60eb60debd94cc3c19fe61604b4cff323b70981"
HK_FACTS_SHA = "08b6cca367119964669bdc9097e33dec8451b54d9f14fd110d237bd0a0d6470c"
HK_ISSUES_SHA = "a4fb351895909b7c5f494bf8b6c4d5413069ab291bd7af6d747a35796b22688b"
HK_REPORT_SHA = "cac2f94f3d1c2eb4add0de138182b19f1020c7ef33ff56e5988b683a03b09b8f"
HK_SNAPSHOT_SHA = "ea19aef05c941de97fe6b71b36a038ab29e69249c091b75f5ae2ade79a320ed8"

STAGE_FILES = {
    "p3_artifact_dir": ("document.json", "pages.jsonl", "sections.jsonl"),
    "p5_artifact_dir": ("table_manifest.json", "tables.jsonl", "table_groups.jsonl"),
    "p6_artifact_dir": ("fact_manifest.json", "raw_facts.jsonl", "evidence.jsonl"),
    "p7_artifact_dir": ("validation_report.json", "issues.jsonl"),
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fingerprint(path: Path) -> dict[str, Any]:
    stat = path.stat()
    return {
        "sha256": sha256_file(path),
        "size": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
    }


def canonical_base_files(project_root: Path, catalog_path: Path) -> tuple[Path, ...]:
    raw = json.loads(catalog_path.read_text(encoding="utf-8"))
    documents = raw.get("documents")
    assert isinstance(documents, list) and len(documents) == 2
    seen = {str(item.get("document_sha256")) for item in documents}
    assert seen == {CN_SHA, HK_SHA}
    paths: list[Path] = [catalog_path]
    for document in documents:
        for field, names in STAGE_FILES.items():
            directory = project_root / str(document[field])
            for name in names:
                path = directory / name
                assert path.is_file(), path
                paths.append(path)
    assert len(paths) == 23
    return tuple(paths)


def snapshot_base(paths: tuple[Path, ...]) -> dict[str, dict[str, Any]]:
    return {str(path): fingerprint(path) for path in paths}


def timed(callable_obj, *args):
    start = time.perf_counter()
    value = callable_obj(*args)
    return value, time.perf_counter() - start


def read_jsonl_row(path: Path, key: str, value: str) -> dict[str, Any]:
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line:
            continue
        row = json.loads(line)
        if str(row.get(key)) == value:
            return row
    raise AssertionError(f"{key}={value} not found in {path}")


def assert_hash(path: Path, expected: str) -> None:
    actual = sha256_file(path)
    assert actual == expected, (path, expected, actual)


def run_document(
    project_root: Path,
    catalog_path: Path,
    review_root: Path,
    document_sha: str,
):
    artifact, prepare_first = timed(
        prepare_review_overlay,
        project_root,
        catalog_path,
        document_sha,
        review_root,
    )
    reused, prepare_reuse = timed(
        prepare_review_overlay,
        project_root,
        catalog_path,
        document_sha,
        review_root,
    )
    assert artifact.to_dict() == reused.to_dict()
    return artifact, prepare_first, prepare_reuse


def run_security_probe() -> None:
    blocked = [
        "https://attacker.example/path",
        r"C:\\secret.txt",
        r"path=C:\\secret.txt",
        "/tmp",
        "/etc/passwd",
        "../secret",
        "powershell",
        "pwsh",
        "bash",
        "curl",
        "wget",
        "powershell -Command Get-ChildItem",
        "bash -lc id",
        "SELECT * FROM secrets",
        "SELECT revenue FROM secrets",
        "UPDATE ledger SET amount = 1",
        "PRAGMA",
        "import os",
        "os.system('whoami')",
        "subprocess.run(['whoami'])",
        "token=secret-value",
    ]
    allowed = [
        "2024/2025",
        "P5/P6 evidence checked",
        "SQL review completed",
        "Select revenue from the annual report evidence.",
        "Update guidance set by management.",
        "Reviewer confirmed powershell was not used.",
    ]
    for value in blocked:
        try:
            validate_resolution_payload_security({"value": value})
        except ReviewError as exc:
            assert exc.reason_code == "P9_RESOLUTION_CONTENT_FORBIDDEN"
            assert str(exc) == "resolution payload contains forbidden content"
            assert value not in str(exc)
        else:
            raise AssertionError(f"forbidden content allowed: {value!r}")
    for value in allowed:
        validate_resolution_payload_security({"value": value})


def run_cli_probe(source_root: Path) -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(source_root / "src")
    cases = [
        [],
        ["unknown-command"],
        ["tasks"],
        [
            "submit",
            "--review-dir",
            "ignored",
            "--input-json",
            "{}",
            "--input-file",
            "ignored.json",
        ],
        ["--help"],
        ["-h"],
        ["tasks", "--help"],
        ["tasks", "-h"],
    ]
    expected = (
        '{"message":"invalid command line arguments",'
        '"reason_code":"P9_CLI_ARGUMENT_ERROR","status":"ERROR"}\n'
    )
    for args in cases:
        result = subprocess.run(
            [
                sys.executable,
                "-B",
                "-m",
                "financial_filing_data_foundation.review.cli",
                *args,
            ],
            cwd=source_root,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 2, (args, result.returncode)
        assert result.stdout == "", (args, result.stdout)
        assert result.stderr == expected, (args, result.stderr)

    runtime = subprocess.run(
        [
            sys.executable,
            "-B",
            "-m",
            "financial_filing_data_foundation.review.cli",
            "tasks",
            "--review-dir",
            str(source_root / "does-not-exist"),
        ],
        cwd=source_root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert runtime.returncode == 1
    assert runtime.stdout == ""
    payload = json.loads(runtime.stderr)
    assert payload["status"] == "ERROR"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--source-root", required=True)
    parser.add_argument("--catalog", required=True)
    parser.add_argument("--work-root", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    source_root = Path(args.source_root).resolve()
    catalog_path = Path(args.catalog).resolve()
    work_root = Path(args.work_root).resolve()
    output = Path(args.output).resolve()

    assert project_root == Path(r"D:\Codex\FinancialFilingDataFoundation").resolve()
    source_root.relative_to(project_root)
    work_root.relative_to(project_root)
    output.relative_to(project_root)
    assert (source_root / "src" / "financial_filing_data_foundation").is_dir()
    assert catalog_path.is_file()
    assert sha256_file(catalog_path) == CATALOG_SHA256
    assert not work_root.exists(), f"fresh work root required: {work_root}"
    work_root.mkdir(parents=True)
    output.parent.mkdir(parents=True, exist_ok=True)
    assert not output.exists(), f"fresh output required: {output}"

    run_security_probe()
    run_cli_probe(source_root)

    base_paths = canonical_base_files(project_root, catalog_path)
    before = snapshot_base(base_paths)

    cn_root = work_root / "cn"
    hk_root = work_root / "hk"

    cn, cn_prepare_first, cn_prepare_reuse = run_document(
        project_root, catalog_path, cn_root, CN_SHA
    )
    cn_tasks = list_review_tasks(cn.review_dir)
    assert len(cn_tasks) == 1
    cn_task = cn_tasks[0]
    assert cn_task.review_task_id == CN_TASK_ID
    assert cn_task.issue_id == CN_ISSUE_ID
    assert cn_task.reason_code == "RAW_PERIOD_COVERAGE_LOW"
    assert tuple(cn_task.supported_actions) == ("SET_PERIOD",)
    assert_hash(cn.review_dir / "review_queue.jsonl", CN_QUEUE_SHA)

    submission = ResolutionSubmission.from_dict(
        {
            "review_task_id": CN_TASK_ID,
            "action": "SET_PERIOD",
            "target": {
                "target_type": "FACT_FIELD",
                "raw_fact_id": CN_FACT_ID,
                "field": "period",
            },
            "value": "2024",
            "evidence_refs": [
                {
                    "type": "P5_CELL",
                    "table_id": CN_TABLE_ID,
                    "cell_id": CN_CELL_ID,
                }
            ],
            "reviewer_type": "CODEX",
            "reviewer_id": "p9-live-validation",
            "reviewed_at": "2026-11-04T09:00:00+09:00",
            "justification": "P5 同表标题明确包含 2024，支持该 raw-null fact 的有效期间标签。",
        }
    )
    cn_resolution, cn_submit = timed(submit_resolution, cn.review_dir, submission)
    assert cn_resolution.resolution_id == CN_RESOLUTION_ID
    assert_hash(
        cn.review_dir / "resolutions" / f"{CN_RESOLUTION_ID}.json",
        CN_RESOLUTION_SHA,
    )
    cn_snapshot, cn_materialize = timed(materialize_resolved_view, cn.review_dir)
    loaded_cn, cn_load = timed(
        load_resolved_snapshot, cn_snapshot.snapshot_dir, cn.review_dir
    )
    assert loaded_cn.overlay_set_hash == CN_OVERLAY_HASH
    assert loaded_cn.resolved_validation_status.value == "REVIEW_REQUIRED"
    assert loaded_cn.resolved_reuse_eligible is False
    assert loaded_cn.active_resolution_count == 1
    cn_fact = read_jsonl_row(loaded_cn.resolved_facts_path, "raw_fact_id", CN_FACT_ID)
    assert cn_fact["raw_period_label"] is None
    assert cn_fact["effective_period_label"] == "2024"
    assert cn_fact["overlay_resolution_ids"] == [CN_RESOLUTION_ID]
    assert_hash(loaded_cn.resolved_facts_path, CN_FACTS_SHA)
    assert_hash(loaded_cn.resolved_issues_path, CN_ISSUES_SHA)
    assert_hash(loaded_cn.report_path, CN_REPORT_SHA)
    assert_hash(loaded_cn.manifest_path, CN_SNAPSHOT_SHA)

    hk, hk_prepare_first, hk_prepare_reuse = run_document(
        project_root, catalog_path, hk_root, HK_SHA
    )
    hk_tasks = list_review_tasks(hk.review_dir)
    assert len(hk_tasks) == 4
    assert {task.reason_code for task in hk_tasks} == HK_REASONS
    assert len(list_resolutions(hk.review_dir)) == 0
    assert_hash(hk.review_dir / "review_queue.jsonl", HK_QUEUE_SHA)
    hk_snapshot, hk_materialize = timed(materialize_resolved_view, hk.review_dir)
    loaded_hk, hk_load = timed(
        load_resolved_snapshot, hk_snapshot.snapshot_dir, hk.review_dir
    )
    assert loaded_hk.overlay_set_hash == HK_OVERLAY_HASH
    assert loaded_hk.resolved_validation_status.value == "REVIEW_REQUIRED"
    assert loaded_hk.resolved_reuse_eligible is False
    assert loaded_hk.active_resolution_count == 0
    assert_hash(loaded_hk.resolved_facts_path, HK_FACTS_SHA)
    assert_hash(loaded_hk.resolved_issues_path, HK_ISSUES_SHA)
    assert_hash(loaded_hk.report_path, HK_REPORT_SHA)
    assert_hash(loaded_hk.manifest_path, HK_SNAPSHOT_SHA)

    timings = {
        "cn_prepare_first": cn_prepare_first,
        "cn_prepare_reuse": cn_prepare_reuse,
        "cn_submit": cn_submit,
        "cn_materialize": cn_materialize,
        "cn_load": cn_load,
        "hk_prepare_first": hk_prepare_first,
        "hk_prepare_reuse": hk_prepare_reuse,
        "hk_materialize": hk_materialize,
        "hk_load": hk_load,
    }
    assert cn_prepare_first <= 20
    assert hk_prepare_first <= 20
    assert cn_prepare_reuse <= 2
    assert hk_prepare_reuse <= 2
    assert cn_submit <= 2
    assert cn_materialize <= 10
    assert hk_materialize <= 10
    assert cn_load <= 10
    assert hk_load <= 10

    after = snapshot_base(base_paths)
    changed = [
        path for path in sorted(before)
        if before[path] != after[path]
    ]
    assert changed == []

    report = {
        "status": "PASS",
        "security_probe": "PASS",
        "cli_probe": "PASS",
        "catalog_sha256": CATALOG_SHA256,
        "base_file_count": len(base_paths),
        "base_changed": changed,
        "cn": {
            "queue_count": len(cn_tasks),
            "queue_sha256": CN_QUEUE_SHA,
            "resolution_id": CN_RESOLUTION_ID,
            "overlay_set_hash": loaded_cn.overlay_set_hash,
            "resolved_status": loaded_cn.resolved_validation_status.value,
            "resolved_reuse_eligible": loaded_cn.resolved_reuse_eligible,
        },
        "hk": {
            "queue_count": len(hk_tasks),
            "reason_set": sorted(HK_REASONS),
            "queue_sha256": HK_QUEUE_SHA,
            "active_resolution_count": loaded_hk.active_resolution_count,
            "overlay_set_hash": loaded_hk.overlay_set_hash,
            "resolved_status": loaded_hk.resolved_validation_status.value,
            "resolved_reuse_eligible": loaded_hk.resolved_reuse_eligible,
        },
        "timings_seconds": timings,
    }
    output.write_text(
        json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
