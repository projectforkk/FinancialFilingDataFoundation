from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence

from .models import ResolutionSubmission, ReviewError
from .queue import list_review_tasks, prepare_review_overlay
from .resolve import materialize_resolved_view
from .store import list_resolutions, submit_resolution


def _json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _submission_payload(args: argparse.Namespace) -> dict[str, Any]:
    if args.input_json is not None:
        try:
            value = json.loads(args.input_json)
        except json.JSONDecodeError as exc:
            raise ReviewError(
                "P9_INVALID_RESOLUTION",
                f"input JSON is invalid: {exc}",
            ) from exc
    else:
        path = Path(args.input_file).expanduser().resolve()
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ReviewError(
                "P9_INVALID_RESOLUTION",
                f"cannot read resolution input file: {exc}",
            ) from exc
    if not isinstance(value, dict):
        raise ReviewError(
            "P9_INVALID_RESOLUTION",
            "resolution input must be a JSON object",
        )
    return value


class _JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise ReviewError(
            "P9_CLI_ARGUMENT_ERROR",
            "invalid command line arguments",
        )


def _build_parser() -> argparse.ArgumentParser:
    parser = _JsonArgumentParser(
        prog="python -m financial_filing_data_foundation.review.cli",
        description="FFDF P9 deterministic review overlay CLI",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    prepare = sub.add_parser("prepare")
    prepare.add_argument("--project-root", required=True)
    prepare.add_argument("--catalog", required=True)
    prepare.add_argument("--document-sha256", required=True)
    prepare.add_argument("--review-root", required=True)

    tasks = sub.add_parser("tasks")
    tasks.add_argument("--review-dir", required=True)

    submit = sub.add_parser("submit")
    submit.add_argument("--review-dir", required=True)
    source = submit.add_mutually_exclusive_group(required=True)
    source.add_argument("--input-json")
    source.add_argument("--input-file")

    resolutions = sub.add_parser("resolutions")
    resolutions.add_argument("--review-dir", required=True)

    materialize = sub.add_parser("materialize")
    materialize.add_argument("--review-dir", required=True)

    report = sub.add_parser("report")
    report.add_argument("--review-dir", required=True)

    return parser


def _run(args: argparse.Namespace) -> Any:
    if args.command == "prepare":
        return prepare_review_overlay(
            args.project_root,
            args.catalog,
            args.document_sha256,
            args.review_root,
        ).to_dict()
    if args.command == "tasks":
        return [task.to_dict() if hasattr(task, "to_dict") else {
            "review_task_id": task.review_task_id,
            "document_sha256": task.document_sha256,
            "base_validation_report_sha256": task.base_validation_report_sha256,
            "issue_id": task.issue_id,
            "reason_code": task.reason_code,
            "message": task.message,
            "observed": task.observed,
            "reviewability": task.reviewability.value,
            "supported_actions": list(task.supported_actions),
            "required_evidence_types": list(task.required_evidence_types),
            "scope": task.scope,
            "page_no": task.page_no,
            "table_id": task.table_id,
            "raw_fact_ids": list(task.raw_fact_ids),
            "evidence_ids": list(task.evidence_ids),
        } for task in list_review_tasks(args.review_dir)]
    if args.command == "submit":
        submission = ResolutionSubmission.from_dict(_submission_payload(args))
        return submit_resolution(args.review_dir, submission).to_dict()
    if args.command == "resolutions":
        return [item.to_dict() for item in list_resolutions(args.review_dir)]
    if args.command == "materialize":
        return materialize_resolved_view(args.review_dir).to_dict()
    if args.command == "report":
        return materialize_resolved_view(args.review_dir).report
    raise AssertionError(f"unhandled command: {args.command}")


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    try:
        args = parser.parse_args(argv)
        result = _run(args)
    except ReviewError as exc:
        print(
            _json(
                {
                    "status": "ERROR",
                    "reason_code": exc.reason_code,
                    "message": str(exc),
                }
            ),
            file=sys.stderr,
        )
        return 2 if exc.reason_code == "P9_CLI_ARGUMENT_ERROR" else 1
    except Exception as exc:
        print(
            _json(
                {
                    "status": "ERROR",
                    "reason_code": "P9_CLI_FAILED",
                    "message": str(exc),
                }
            ),
            file=sys.stderr,
        )
        return 1

    print(_json({"status": "OK", "data": result}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
