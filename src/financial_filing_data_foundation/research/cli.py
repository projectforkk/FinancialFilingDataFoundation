from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

from financial_filing_data_foundation.mcp import CatalogError, McpCatalog

from .context import build_research_context
from .models import P10Error, ResearchSpecBundle, ResearchSpecInput
from .provenance import EvidenceLedger, validate_evidence_ledger
from .spec import freeze_research_spec, verify_research_spec


MAX_STDIN_BYTES = 16 * 1024 * 1024
COMMANDS = (
    "freeze-spec",
    "verify-spec",
    "build-context",
    "validate-ledger",
)


def _json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


class _JsonArgumentParser(argparse.ArgumentParser):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs.setdefault("add_help", False)
        kwargs.setdefault("allow_abbrev", False)
        super().__init__(*args, **kwargs)

    def error(self, message: str) -> None:
        raise P10Error(
            "P10_CLI_ARGUMENT_ERROR",
            "invalid command line arguments",
        )


def _build_parser() -> argparse.ArgumentParser:
    parser = _JsonArgumentParser(
        prog="python -m financial_filing_data_foundation.research.cli",
        description="FFDF P10 deterministic research integration CLI",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    freeze = sub.add_parser("freeze-spec")
    freeze.add_argument("--project-root", required=True)

    verify = sub.add_parser("verify-spec")
    verify.add_argument("--project-root", required=True)

    build = sub.add_parser("build-context")
    build.add_argument("--project-root", required=True)
    build.add_argument("--catalog", required=True)
    build.add_argument("--p9-review-root", required=True)

    validate = sub.add_parser("validate-ledger")
    validate.add_argument("--project-root", required=True)
    validate.add_argument("--catalog", required=True)
    validate.add_argument("--p9-review-root", required=True)

    return parser


def _command_hint(argv: Sequence[str]) -> str | None:
    if argv and argv[0] in COMMANDS:
        return argv[0]
    return None


def _read_request() -> dict[str, Any]:
    raw = sys.stdin.buffer.read(MAX_STDIN_BYTES + 1)
    if not raw:
        raise P10Error(
            "P10_CLI_INPUT_INVALID",
            "stdin request must be a non-empty JSON object",
        )
    if len(raw) > MAX_STDIN_BYTES:
        raise P10Error(
            "P10_CLI_INPUT_INVALID",
            "stdin request exceeds 16 MiB",
        )
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise P10Error(
            "P10_CLI_INPUT_INVALID",
            "stdin request must be UTF-8 JSON",
        ) from exc
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        raise P10Error(
            "P10_CLI_INPUT_INVALID",
            "stdin request is invalid JSON",
        ) from exc
    if not isinstance(value, dict):
        raise P10Error(
            "P10_CLI_INPUT_INVALID",
            "stdin request root must be a JSON object",
        )
    return value


def _exact_keys(
    value: Mapping[str, Any],
    expected: set[str],
    label: str,
) -> None:
    if set(value) != expected:
        raise P10Error(
            "P10_CLI_INPUT_INVALID",
            f"{label} fields are invalid",
        )


def _spec_bundle(value: Any) -> ResearchSpecBundle:
    return ResearchSpecBundle.from_dict(value)


def _freeze_inputs(value: Mapping[str, Any]) -> list[ResearchSpecInput]:
    _exact_keys(value, {"files"}, "freeze-spec request")
    files = value.get("files")
    if not isinstance(files, list):
        raise P10Error(
            "P10_CLI_INPUT_INVALID",
            "freeze-spec files must be a list",
        )
    inputs: list[ResearchSpecInput] = []
    for item in files:
        if not isinstance(item, Mapping):
            raise P10Error(
                "P10_CLI_INPUT_INVALID",
                "freeze-spec file entry must be an object",
            )
        _exact_keys(
            item,
            {"logical_name", "relative_path"},
            "freeze-spec file entry",
        )
        inputs.append(
            ResearchSpecInput(
                logical_name=item.get("logical_name"),
                relative_path=item.get("relative_path"),
            )
        )
    return inputs


def _relative_catalog_arg(value: str) -> str:
    if not isinstance(value, str) or not value:
        raise P10Error(
            "P10_CATALOG_INVALID",
            "catalog path must be a non-empty project-root-relative path",
        )
    path = Path(value)
    if path.is_absolute() or path.drive or path.root:
        raise P10Error(
            "P10_CATALOG_INVALID",
            "catalog path must be project-root-relative",
        )
    return value


def _load_catalog(project_root: str, catalog_path: str) -> McpCatalog:
    relative = _relative_catalog_arg(catalog_path)
    try:
        return McpCatalog.load(project_root, relative)
    except CatalogError as exc:
        raise P10Error(
            "P10_CATALOG_INVALID",
            "catalog cannot be loaded",
        ) from exc
    except (OSError, RuntimeError, TypeError, ValueError) as exc:
        raise P10Error(
            "P10_CATALOG_INVALID",
            "catalog cannot be loaded",
        ) from exc


def _run(args: argparse.Namespace, request: Mapping[str, Any]) -> Any:
    if args.command == "freeze-spec":
        files = _freeze_inputs(request)
        return freeze_research_spec(args.project_root, files).to_dict()

    if args.command == "verify-spec":
        _exact_keys(request, {"spec_bundle"}, "verify-spec request")
        bundle = _spec_bundle(request.get("spec_bundle"))
        verify_research_spec(args.project_root, bundle)
        return {
            "spec_bundle_hash": bundle.spec_bundle_hash,
            "verified": True,
        }

    if args.command == "build-context":
        _exact_keys(request, {"spec_bundle"}, "build-context request")
        bundle = _spec_bundle(request.get("spec_bundle"))
        verify_research_spec(args.project_root, bundle)
        catalog = _load_catalog(args.project_root, args.catalog)
        return build_research_context(
            bundle,
            catalog,
            args.p9_review_root,
        ).to_dict()

    if args.command == "validate-ledger":
        _exact_keys(
            request,
            {"spec_bundle", "ledger"},
            "validate-ledger request",
        )
        bundle = _spec_bundle(request.get("spec_bundle"))
        verify_research_spec(args.project_root, bundle)
        catalog = _load_catalog(args.project_root, args.catalog)
        context = build_research_context(
            bundle,
            catalog,
            args.p9_review_root,
        )
        ledger = EvidenceLedger.from_dict(request.get("ledger"))
        return validate_evidence_ledger(
            context,
            ledger,
            bundle,
            catalog,
        ).to_dict()

    raise AssertionError(f"unhandled command: {args.command}")


def _write_json_line(stream: Any, value: Any) -> None:
    text = _json(value) + "\n"
    buffer = getattr(stream, "buffer", None)
    if buffer is None:
        stream.write(text)
        stream.flush()
        return
    buffer.write(text.encode("utf-8"))
    buffer.flush()


def _emit_error(
    command: str | None,
    reason_code: str,
    message: str,
) -> None:
    _write_json_line(
        sys.stderr,
        {
            "command": command,
            "message": message,
            "reason_code": reason_code,
            "status": "ERROR",
        },
    )


def main(argv: Sequence[str] | None = None) -> int:
    selected_argv = list(sys.argv[1:] if argv is None else argv)
    command = _command_hint(selected_argv)
    parser = _build_parser()

    try:
        args = parser.parse_args(selected_argv)
        command = args.command
        request = _read_request()
        data = _run(args, request)
    except P10Error as exc:
        _emit_error(command, exc.reason_code, str(exc))
        return 2 if exc.reason_code == "P10_CLI_ARGUMENT_ERROR" else 1
    except Exception:
        _emit_error(
            command,
            "P10_CLI_FAILED",
            "unexpected CLI failure",
        )
        return 1

    _write_json_line(
        sys.stdout,
        {
            "command": command,
            "data": data,
            "status": "OK",
        },
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
