from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import sys
import tempfile
from dataclasses import dataclass, replace
from datetime import date
from pathlib import Path
from typing import Any

from financial_filing_data_foundation.acquisition import (
    AcquisitionError,
    AcquisitionRequest,
    AcquisitionStatus,
    DAYU_PACKAGE_VERSION,
    DAYU_PINNED_COMMIT,
    DAYU_REPOSITORY,
    DayuRuntimeDescriptor,
    DayuSubprocessAdapter,
    RawDocumentStore,
    acquire_slot,
)
from financial_filing_data_foundation.candidates import detect_table_candidates
from financial_filing_data_foundation.facts import extract_raw_facts
from financial_filing_data_foundation.identity import CompanyRef, FilingSlotKey
from financial_filing_data_foundation.mcp.catalog import McpCatalog
from financial_filing_data_foundation.mcp.service import McpQueryService
from financial_filing_data_foundation.native import parse_native_document
from financial_filing_data_foundation.registry import SQLiteRegistry
from financial_filing_data_foundation.tables import reconstruct_tables
from financial_filing_data_foundation.validation import (
    build_parsed_data_record,
    validate_document_artifacts,
)
from financial_filing_data_foundation.us_sec.acquisition import SecAcquirer, candidate_from_package
from financial_filing_data_foundation.us_sec.errors import SecError
from financial_filing_data_foundation.us_sec.feature_gate import require_us_development
from financial_filing_data_foundation.us_sec.http import SecHttpClient, SecHttpConfig
from financial_filing_data_foundation.us_sec.identity import normalize_cik, sec_company
from financial_filing_data_foundation.us_sec.ingest import ingest_sec_package
from financial_filing_data_foundation.us_sec.package import SecPackageStore
from financial_filing_data_foundation.us_sec.planner import SecPlan, SecPlanAction, plan_sec_slot
from financial_filing_data_foundation.us_sec.registry import register_sec_package, register_sec_slot
from financial_filing_data_foundation.us_sec.runtime import SecRuntimeDescriptor, SecSubprocessTransport
from financial_filing_data_foundation.us_sec.ticker_map import parse_ticker_map, snapshot_ticker_map


_PERIODS = ("Q1", "Q2", "H1", "Q3", "FY")
_IDENTITY_FILING_TYPE = {
    "Q1": "QUARTERLY_REPORT",
    "H1": "INTERIM_REPORT",
    "Q3": "QUARTERLY_REPORT",
    "FY": "ANNUAL_REPORT",
}
_CATALOG_FILING_TYPE = {
    "Q1": "Q1",
    "H1": "H1",
    "Q3": "Q3",
    "FY": "ANNUAL",
}


@dataclass(frozen=True)
class RuntimePaths:
    root: Path
    ingest_root: Path
    raw_store: Path
    registry: Path
    acquisition_workspace: Path
    catalog: Path
    dayu_python: Path
    dayu_source: Path
    dayu_runner: Path


def _project_root() -> Path:
    env = os.environ.get("FFDF_ROOT")
    if env:
        return Path(env).expanduser().resolve()
    return Path(__file__).resolve().parents[2]


def _runtime_paths(root: Path) -> RuntimePaths:
    ingest = root / "workspace" / "ingest"
    return RuntimePaths(
        root=root,
        ingest_root=ingest,
        raw_store=ingest / "raw-store",
        registry=ingest / "registry.sqlite",
        acquisition_workspace=ingest / "acquisition-workspace",
        catalog=root / "workspace" / "mcp" / "p8-live-catalog.json",
        dayu_python=(
            root
            / "runtimes"
            / "ffdf-dayu-2115c86"
            / ".venv"
            / "Scripts"
            / "python.exe"
        ),
        dayu_source=root / "dependencies" / "dayu-agent",
        dayu_runner=(
            root
            / "src"
            / "financial_filing_data_foundation"
            / "acquisition"
            / "dayu_runner.py"
        ),
    )


def _period(value: str) -> str:
    period = value.strip().upper()
    if period not in _PERIODS:
        raise argparse.ArgumentTypeError(
            f"period must be one of {', '.join(_PERIODS)}"
        )
    return period


def _validate_market_period(args: argparse.Namespace) -> None:
    market = str(args.market).strip().upper()
    period = str(args.period).strip().upper()
    allowed = {"Q1", "Q2", "Q3", "FY"} if market == "US" else {"Q1", "H1", "Q3", "FY"}
    if period not in allowed:
        raise ValueError(f"period {period} is not supported for market {market}")


def _default_window(year: int, period: str) -> tuple[str, str]:
    if period == "Q1":
        start = date(year, 3, 1)
        end = date(year, 5, 31)
    elif period == "Q2":
        start = date(year, 6, 1)
        end = date(year, 8, 31)
    elif period == "H1":
        start = date(year, 6, 1)
        end = date(year, 9, 30)
    elif period == "Q3":
        start = date(year, 9, 1)
        end = date(year, 11, 30)
    else:
        start = date(year + 1, 1, 1)
        end = date(year + 1, 6, 30)

    today = date.today()
    if start > today:
        raise ValueError(
            "default publication search window has not started yet; "
            "use --window-start/--window-end only when you intentionally "
            "need a different official-publication window"
        )
    if end > today:
        end = today
    return start.isoformat(), end.isoformat()


def _window(args: argparse.Namespace) -> tuple[str, str]:
    if bool(args.window_start) != bool(args.window_end):
        raise ValueError("--window-start and --window-end must be supplied together")
    if args.window_start:
        start = date.fromisoformat(args.window_start)
        end = date.fromisoformat(args.window_end)
        if start > end:
            raise ValueError("--window-start must be <= --window-end")
        return start.isoformat(), end.isoformat()
    return _default_window(args.year, args.period)


def _request(args: argparse.Namespace) -> AcquisitionRequest:
    market = args.market.upper()
    _validate_market_period(args)
    if market not in {"CN", "HK"}:
        raise ValueError("US requests use the SEC provider path")
    if not args.ticker or not args.ticker.strip():
        raise ValueError("--ticker is required for CN/HK")
    ticker = args.ticker.strip()
    company_id = args.company_id or f"{market}:{ticker}"
    filing_type = args.filing_type or _IDENTITY_FILING_TYPE[args.period]
    window_start, window_end = _window(args)

    company = CompanyRef(
        market=market,
        company_id=company_id,
        ticker=ticker,
    )
    slot = FilingSlotKey(
        market=market,
        company_id=company_id,
        filing_type=filing_type,
        fiscal_year=args.year,
        raw_fiscal_period=args.period,
    )
    return AcquisitionRequest(
        company=company,
        slot=slot,
        window_start=window_start,
        window_end=window_end,
    )


def _provider(paths: RuntimePaths) -> DayuSubprocessAdapter:
    for required in (paths.dayu_python, paths.dayu_source, paths.dayu_runner):
        if not required.exists():
            raise FileNotFoundError(required)
    runtime = DayuRuntimeDescriptor(
        dayu_repository=DAYU_REPOSITORY,
        dayu_commit=DAYU_PINNED_COMMIT,
        dayu_package_version=DAYU_PACKAGE_VERSION,
        dayu_source_path=paths.dayu_source,
        dayu_python_executable=paths.dayu_python,
    )
    return DayuSubprocessAdapter(
        runtime=runtime,
        runner_script=paths.dayu_runner,
        workspace_root=paths.acquisition_workspace,
        doctor_timeout_seconds=60.0,
        operation_timeout_seconds=300.0,
    )


def _relative(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _catalog_document(
    root: Path,
    request: AcquisitionRequest,
    sha: str,
    p3: Path,
    p5: Path,
    p6: Path,
    p7: Path,
) -> dict[str, Any]:
    return {
        "document_sha256": sha,
        "market": request.slot.market,
        "ticker": request.company.ticker,
        "fiscal_year": request.slot.fiscal_year,
        "filing_type": _CATALOG_FILING_TYPE[request.slot.raw_fiscal_period],
        "p3_artifact_dir": _relative(root, p3),
        "p5_artifact_dir": _relative(root, p5),
        "p6_artifact_dir": _relative(root, p6),
        "p7_artifact_dir": _relative(root, p7),
    }


def _upsert_catalog(
    paths: RuntimePaths,
    document: dict[str, Any],
    *,
    verify_document: bool = True,
) -> str:
    paths.catalog.parent.mkdir(parents=True, exist_ok=True)
    if paths.catalog.exists():
        payload = json.loads(paths.catalog.read_text(encoding="utf-8"))
    else:
        payload = {"schema_version": "p8-mcp-catalog-v1", "documents": []}

    if payload.get("schema_version") != "p8-mcp-catalog-v1":
        raise RuntimeError("P8 catalog schema_version mismatch")
    documents = payload.get("documents")
    if not isinstance(documents, list):
        raise RuntimeError("P8 catalog documents must be a list")

    identity = (
        document["market"].upper(),
        document["ticker"].upper(),
        int(document["fiscal_year"]),
        document["filing_type"].upper(),
    )
    sha = document["document_sha256"].lower()

    replacement_index: int | None = None
    for index, existing in enumerate(documents):
        existing_sha = str(existing.get("document_sha256", "")).lower()
        existing_identity = (
            str(existing.get("market", "")).upper(),
            str(existing.get("ticker", "")).upper(),
            int(existing.get("fiscal_year", 0)),
            str(existing.get("filing_type", "")).upper(),
        )
        if existing_sha == sha and existing_identity != identity:
            raise RuntimeError(
                "P8 catalog SHA is already bound to a different filing identity"
            )
        if existing_identity == identity:
            if existing_sha != sha:
                raise RuntimeError(
                    "P8 catalog filing identity already points to a different SHA; "
                    "manual review is required"
                )
            replacement_index = index
            break

    if replacement_index is None:
        documents.append(document)
        action = "ADDED"
    else:
        documents[replacement_index] = document
        action = "ALREADY_REGISTERED"

    documents.sort(
        key=lambda row: (
            str(row["market"]).upper(),
            str(row["ticker"]).upper(),
            int(row["fiscal_year"]),
            str(row["filing_type"]).upper(),
            str(row["document_sha256"]).lower(),
        )
    )

    candidate = {
        "schema_version": "p8-mcp-catalog-v1",
        "documents": documents,
    }
    text = json.dumps(candidate, ensure_ascii=False, indent=2) + "\n"

    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        newline="\n",
        dir=paths.catalog.parent,
        prefix=".p8-live-catalog.",
        suffix=".tmp",
        delete=False,
    ) as handle:
        temp = Path(handle.name)
        handle.write(text)

    try:
        catalog = McpCatalog.load(paths.root, temp)
        if verify_document:
            McpQueryService(catalog).get_document(sha)
        os.replace(temp, paths.catalog)
    finally:
        if temp.exists():
            temp.unlink()
    return action


def _common_payload(request: AcquisitionRequest) -> dict[str, Any]:
    return {
        "market": request.slot.market,
        "ticker": request.company.ticker,
        "company_id": request.company.company_id,
        "filing_type": request.slot.filing_type,
        "fiscal_year": request.slot.fiscal_year,
        "period": request.slot.raw_fiscal_period,
        "window_start": request.window_start,
        "window_end": request.window_end,
    }


def _persist_ticker_map_snapshot(root: Path, snapshot: Any) -> Path:
    directory = root / "workspace" / "ingest" / "us" / "ticker-map"
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{snapshot.source_sha256}.json"
    if not path.exists():
        path.write_text(
            json.dumps(snapshot.to_dict(), ensure_ascii=False, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
    return path


def _cached_ticker_resolution(root: Path, ticker: str) -> tuple[str, dict[str, str | None]] | None:
    """Resolve a ticker from a previously persisted, byte-provenanced map."""

    normalized = ticker.strip().upper()
    directory = root / "workspace" / "ingest" / "us" / "ticker-map"
    matches: list[tuple[str, dict[str, str | None]]] = []
    if not directory.is_dir():
        return None
    for path in sorted(directory.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            continue
        mapping = payload.get("mapping") if isinstance(payload, dict) else None
        values = mapping.get(normalized) if isinstance(mapping, dict) else None
        if isinstance(values, str):
            values = [values]
        if not isinstance(values, list):
            continue
        try:
            ciks = sorted({normalize_cik(str(value)) for value in values})
        except SecError:
            continue
        if len(ciks) > 1:
            raise SecError("P11_TICKER_CIK_AMBIGUOUS", f"cached ticker maps to multiple CIKs: {normalized}")
        if not ciks:
            continue
        source_sha256 = str(payload.get("source_sha256") or "").strip().lower()
        source_bytes_b64 = payload.get("source_bytes_b64")
        if not source_sha256 or not isinstance(source_bytes_b64, str):
            continue
        try:
            source_bytes = base64.b64decode(source_bytes_b64, validate=True)
        except (ValueError, TypeError):
            continue
        if hashlib.sha256(source_bytes).hexdigest() != source_sha256:
            continue
        matches.append(
            (
                ciks[0],
                {
                    "source_url": str(payload.get("source_url") or "").strip() or None,
                    "source_sha256": source_sha256,
                    "retrieved_at": str(payload.get("retrieved_at") or "").strip() or None,
                },
            )
        )
    if not matches:
        return None
    ciks = {cik for cik, _ in matches}
    if len(ciks) != 1:
        raise SecError("P11_TICKER_CIK_AMBIGUOUS", f"cached ticker maps to multiple CIKs: {normalized}")
    return max(matches, key=lambda item: (item[1].get("retrieved_at") or "", item[1].get("source_sha256") or ""))


def _us_company_and_client(args: argparse.Namespace) -> tuple[Any, SecHttpClient | None]:
    require_us_development()
    runtime = SecRuntimeDescriptor.for_project(_project_root())
    client: SecHttpClient | None = None
    ticker = args.ticker.strip().upper() if args.ticker else None
    if args.cik:
        cik = normalize_cik(args.cik)
        company = sec_company(cik=cik, ticker=ticker, allow_development=True)
        return company, client
    if not ticker:
        raise SecError("P11_INVALID_US_IDENTITY", "US requires --cik or --ticker")
    cached = _cached_ticker_resolution(_project_root(), ticker)
    if cached is not None:
        cik, provenance = cached
        return sec_company(
            cik=cik,
            ticker=ticker,
            allow_development=True,
            ticker_source_url=provenance["source_url"],
            ticker_source_sha256=provenance["source_sha256"],
            ticker_retrieved_at=provenance["retrieved_at"],
        ), client
    client = SecHttpClient(
        SecHttpConfig.from_env(),
        transport=SecSubprocessTransport(runtime),
    )
    mapping_response = client.fetch(
        "https://www.sec.gov/files/company_tickers.json",
        expected_content_types=("application/json",),
        max_bytes=client.config.submissions_max_bytes,
    )
    cik = parse_ticker_map(mapping_response.body, ticker)
    snapshot = snapshot_ticker_map(
        mapping_response.body,
        source_url="https://www.sec.gov/files/company_tickers.json",
    )
    _persist_ticker_map_snapshot(_project_root(), snapshot)
    return sec_company(
        cik=cik,
        ticker=ticker,
        allow_development=True,
        ticker_source_url=snapshot.source_url,
        ticker_source_sha256=snapshot.source_sha256,
        ticker_retrieved_at=snapshot.retrieved_at,
    ), client


def _us_plan_slot(
    company: Any,
    args: argparse.Namespace,
    paths: RuntimePaths,
    registry: SQLiteRegistry,
) -> tuple[SecPlan, Any | None]:
    bindings = registry.list_sec_bindings(
        company_id=company.company_id,
        fiscal_year=args.year,
        period=args.period,
    )
    amendment_flags = {bool(int(row["amended"] or 0)) for row in bindings}
    amendment_conflict = bool(bindings) and amendment_flags == {False, True}
    store = SecPackageStore(paths.raw_store)
    packages: dict[str, Any] = {}
    for row in bindings:
        try:
            package = store.load(str(row["package_sha256"]))
        except Exception:
            continue
        packages[package.package_sha256] = package
    if not packages:
        local = store.find_by_slot(cik=company.cik, fiscal_year=args.year, period=args.period)
        if local is not None:
            packages[local.package_sha256] = local
    parsed_rows = registry.list_sec_parsed_data(
        company_id=company.company_id,
        fiscal_year=args.year,
        period=args.period,
    )
    parsed_available = bool(packages) and any(
        str(row["validation_status"]).upper() == "PASS"
        and str(row["compatibility_status"]).upper() == "COMPATIBLE"
        and int(row["blocking_issue_count"] or 0) == 0
        and str(row["artifact_path"] or "").strip()
        and (paths.root / str(row["artifact_path"])).resolve().is_dir()
        for row in parsed_rows
    )
    plan = plan_sec_slot(
        parsed_available=parsed_available,
        package_available=bool(packages),
        amendment_conflict=amendment_conflict,
    )
    package = next(iter(packages.values()), None)
    return plan, package


def _us_acquire_result(args: argparse.Namespace) -> tuple[Any, Any, RuntimePaths]:
    root = _project_root()
    paths = _runtime_paths(root)
    company, client = _us_company_and_client(args)
    registry = SQLiteRegistry(paths.registry)
    plan, local_package = _us_plan_slot(company, args, paths, registry)
    if plan.action is SecPlanAction.REVIEW_REQUIRED:
        raise SecError(plan.reason_code or "P11_AMENDED_VARIANT_PRESENT", "SEC slot has an amended variant conflict")
    if local_package is not None and plan.action in {SecPlanAction.REUSE_DATA, SecPlanAction.PARSE_LOCAL}:
        from financial_filing_data_foundation.us_sec.acquisition import SecAcquisitionResult

        result = SecAcquisitionResult(
            package=local_package,
            candidate=candidate_from_package(local_package, company),
            reused=True,
            plan_action=plan.action.value,
        )
        register_sec_package(registry, local_package)
        register_sec_slot(
            registry,
            local_package,
            fiscal_year=args.year,
            period=args.period,
            binding_status="SOURCE_CONFIRMED",
        )
        return company, result, paths
    acquirer = SecAcquirer(
        client
        or SecHttpClient(
            SecHttpConfig.from_env(),
            transport=SecSubprocessTransport(SecRuntimeDescriptor.for_project(root)),
        ),
        SecPackageStore(paths.raw_store),
    )
    result = acquirer.acquire(company, fiscal_year=args.year, period=args.period)
    result = replace(result, plan_action=plan.action.value)
    register_sec_package(registry, result.package)
    register_sec_slot(
        registry,
        result.package,
        fiscal_year=args.year,
        period=args.period,
        binding_status="SOURCE_CONFIRMED",
    )
    return company, result, paths


def _us_acquire(args: argparse.Namespace, *, quiet: bool = False) -> tuple[int, dict[str, Any], Any, RuntimePaths, SQLiteRegistry]:
    company, result, paths = _us_acquire_result(args)
    registry = SQLiteRegistry(paths.registry)
    payload = {
        "command": "acquire",
        "market": "US",
        "ticker": company.ticker,
        "cik": company.cik,
        "company_id": company.company_id,
        "fiscal_year": args.year,
        "period": args.period,
        "planner_action": result.plan_action,
        "status": "REUSED_LOCAL" if result.reused else "DOWNLOADED",
        "reason_code": None,
        "accession": result.candidate.accession,
        "form": result.candidate.form,
        "package_sha256": result.package.package_sha256,
        "raw_path": str(SecPackageStore(paths.raw_store).package_dir(result.package.package_sha256)),
        "provider": "sec",
        "source_id": result.candidate.accession,
    }
    if not quiet:
        _print(payload)
    return 0, payload, result, paths, registry


def _us_ingest(args: argparse.Namespace) -> int:
    company, result, paths = _us_acquire_result(args)
    acquire_payload = {
        "status": "REUSED_LOCAL" if result.reused else "DOWNLOADED",
        "planner_action": result.plan_action,
    }
    ingested = ingest_sec_package(
        result.package,
        root=paths.root,
        ticker=result.candidate.ticker,
        period=args.period,
        company_id=result.candidate.cik and f"US:CIK{result.candidate.cik}",
        ticker_source_url=getattr(company, "ticker_source_url", None),
        ticker_source_sha256=getattr(company, "ticker_source_sha256", None),
        ticker_retrieved_at=getattr(company, "ticker_retrieved_at", None),
    )
    _print(
        {
            "command": "ingest",
            "market": "US",
            "ticker": result.candidate.ticker,
            "cik": result.candidate.cik,
            "fiscal_year": args.year,
            "period": args.period,
            "planner_action": acquire_payload["planner_action"],
            "accession": result.candidate.accession,
            "package_sha256": result.package.package_sha256,
            "validation_status": ingested.validation.validation_status,
            "blocking_issue_count": ingested.validation.blocking_issue_count,
            "review_issue_count": ingested.validation.review_issue_count,
            "p8_catalog": ingested.catalog_status,
            "research_ready": ingested.research_ready,
            "artifact_dir": str(ingested.parsed.artifact_dir),
            "catalog_path": str(ingested.catalog_path),
        }
    )
    return 0 if ingested.research_ready else 6


def _us_status(args: argparse.Namespace) -> int:
    root = _project_root()
    require_us_development()
    if args.cik:
        company = sec_company(cik=normalize_cik(args.cik), ticker=None, allow_development=True)
    else:
        company, _ = _us_company_and_client(args)
    paths = _runtime_paths(root)
    registry = SQLiteRegistry(paths.registry)
    bindings = registry.list_sec_bindings(
        company_id=company.company_id,
        fiscal_year=args.year,
        period=args.period,
    )
    catalog_document: dict[str, Any] | None = None
    if paths.catalog.exists():
        payload = json.loads(paths.catalog.read_text(encoding="utf-8"))
        for row in payload.get("documents", []):
            if (
                str(row.get("market", "")).upper() == "US"
                and str(row.get("company_id") or f"US:CIK{str(row.get('cik') or '').zfill(10)}").upper() == company.company_id.upper()
                and int(row.get("fiscal_year", 0)) == args.year
                and str(row.get("raw_fiscal_period", "")).upper() == args.period
            ):
                catalog_document = row
                break
    _print(
        {
            "command": "status",
            "market": "US",
            "ticker": company.ticker,
            "cik": company.cik,
            "fiscal_year": args.year,
            "period": args.period,
            "bindings": [dict(row) for row in bindings],
            "p8_catalog_registered": catalog_document is not None,
            "p8_catalog_document": catalog_document,
        }
    )
    return 0


def _print(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))


def _acquire(args: argparse.Namespace, *, quiet: bool = False) -> tuple[int, dict[str, Any], AcquisitionRequest, RuntimePaths, SQLiteRegistry]:
    _validate_market_period(args)
    if args.market.upper() == "US":
        return _us_acquire(args, quiet=quiet)  # type: ignore[return-value]
    root = _project_root()
    paths = _runtime_paths(root)
    request = _request(args)
    paths.ingest_root.mkdir(parents=True, exist_ok=True)

    registry = SQLiteRegistry(paths.registry)
    provider = _provider(paths)
    doctor = provider.doctor()

    result = acquire_slot(
        request=request,
        provider=provider,
        raw_store=RawDocumentStore(paths.raw_store),
        registry=registry,
    )

    payload = {
        "command": "acquire",
        **_common_payload(request),
        "dayu_doctor": doctor.get("status", "OK"),
        "status": result.status.value,
        "reason_code": result.reason_code,
        "document_sha256": result.document_sha256,
        "raw_path": None if result.raw_path is None else str(result.raw_path),
        "receipt_path": (
            None if result.receipt_path is None else str(result.receipt_path)
        ),
        "provider": result.provider,
        "source_id": result.source_id,
    }

    if result.status in {AcquisitionStatus.DOWNLOADED, AcquisitionStatus.REUSED_LOCAL}:
        code = 0
    elif result.status == AcquisitionStatus.NOT_FOUND:
        code = 2
    elif result.status == AcquisitionStatus.REVIEW_REQUIRED:
        code = 3
    else:
        code = 4

    if not quiet:
        _print(payload)
    return code, payload, request, paths, registry


def _ingest(args: argparse.Namespace) -> int:
    _validate_market_period(args)
    if args.market.upper() == "US":
        return _us_ingest(args)
    code, acquire_payload, request, paths, registry = _acquire(args, quiet=True)
    if code != 0:
        _print(
            {
                "command": "ingest",
                **_common_payload(request),
                "stage": "ACQUISITION",
                **{k: v for k, v in acquire_payload.items() if k not in {"command"}},
                "research_ready": False,
            }
        )
        return code

    raw_path = Path(str(acquire_payload["raw_path"])).resolve()
    sha = str(acquire_payload["document_sha256"])
    market_dir = request.slot.market.lower()
    base = paths.ingest_root / market_dir

    p3_artifact = parse_native_document(raw_path, base / "p3")
    p4_artifact = detect_table_candidates(
        p3_artifact.artifact_dir,
        base / "p4",
    )
    p5_artifact = reconstruct_tables(
        p3_artifact.artifact_dir,
        p4_artifact.artifact_dir,
        base / "p5",
    )
    p6_artifact = extract_raw_facts(
        p3_artifact.artifact_dir,
        p5_artifact.artifact_dir,
        base / "p6",
    )
    p7_artifact = validate_document_artifacts(
        p3_artifact.artifact_dir,
        p5_artifact.artifact_dir,
        p6_artifact.artifact_dir,
        base / "p7",
    )

    record = build_parsed_data_record(
        p7_artifact,
        request.slot,
        _relative(paths.root, p7_artifact.artifact_dir),
    )
    registry.register_parsed_data(record)

    catalog_status = "NOT_REGISTERED_BLOCKING_VALIDATION"
    research_ready = False
    if p7_artifact.blocking_issue_count == 0:
        document = _catalog_document(
            paths.root,
            request,
            sha,
            p3_artifact.artifact_dir,
            p5_artifact.artifact_dir,
            p6_artifact.artifact_dir,
            p7_artifact.artifact_dir,
        )
        catalog_status = _upsert_catalog(paths, document)
        research_ready = True

    payload = {
        "command": "ingest",
        **_common_payload(request),
        "acquisition_status": acquire_payload["status"],
        "document_sha256": sha,
        "raw_path": str(raw_path),
        "p3": {
            "status": "PASS",
            "page_count": p3_artifact.page_count,
            "artifact_dir": str(p3_artifact.artifact_dir),
        },
        "p4": {
            "status": "PASS",
            "candidate_count": p4_artifact.candidate_count,
            "artifact_dir": str(p4_artifact.artifact_dir),
        },
        "p5": {
            "status": "PASS",
            "table_count": p5_artifact.table_count,
            "group_count": p5_artifact.group_count,
            "artifact_dir": str(p5_artifact.artifact_dir),
        },
        "p6": {
            "status": "PASS",
            "fact_count": p6_artifact.fact_count,
            "evidence_count": p6_artifact.evidence_count,
            "artifact_dir": str(p6_artifact.artifact_dir),
        },
        "p7": {
            "validation_status": p7_artifact.validation_status.value,
            "compatibility_status": p7_artifact.compatibility_status.value,
            "blocking_issue_count": p7_artifact.blocking_issue_count,
            "review_issue_count": p7_artifact.review_issue_count,
            "warning_issue_count": p7_artifact.warning_issue_count,
            "reuse_eligible": p7_artifact.reuse_eligible,
            "artifact_dir": str(p7_artifact.artifact_dir),
        },
        "registry": "REGISTERED",
        "p8_catalog": catalog_status,
        "catalog_path": str(paths.catalog),
        "research_ready": research_ready,
    }
    _print(payload)
    return 0 if research_ready else 6


def _status(args: argparse.Namespace) -> int:
    _validate_market_period(args)
    if args.market.upper() == "US":
        return _us_status(args)
    root = _project_root()
    paths = _runtime_paths(root)
    request = _request(args)
    registry = SQLiteRegistry(paths.registry)

    local = registry.resolve_local_document(request.slot)
    parsed = registry.list_parsed_data(request.slot)

    catalog_match: dict[str, Any] | None = None
    if paths.catalog.exists():
        payload = json.loads(paths.catalog.read_text(encoding="utf-8"))
        expected_type = _CATALOG_FILING_TYPE[request.slot.raw_fiscal_period]
        for document in payload.get("documents", []):
            if (
                str(document.get("market", "")).upper() == request.slot.market
                and str(document.get("ticker", "")).upper()
                == request.company.ticker.upper()
                and int(document.get("fiscal_year", 0)) == request.slot.fiscal_year
                and str(document.get("filing_type", "")).upper() == expected_type
            ):
                catalog_match = document
                break

    _print(
        {
            "command": "status",
            **_common_payload(request),
            "local_document_status": local.status.value,
            "document_sha256": local.document_sha256,
            "raw_path": (
                None if local.canonical_path is None else str(local.canonical_path)
            ),
            "parsed_runs": [
                {
                    "parse_run_id": row.parse_run_id,
                    "document_sha256": row.document_sha256,
                    "validation_status": row.validation_status.value,
                    "compatibility_status": row.compatibility_status.value,
                    "blocking_issue_count": row.blocking_issue_count,
                    "artifact_path": row.artifact_path,
                }
                for row in parsed
            ],
            "p8_catalog_registered": catalog_match is not None,
            "p8_catalog_document": catalog_match,
        }
    )
    return 0


def _add_filing_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--market", required=True, choices=("CN", "HK", "US"))
    parser.add_argument("--ticker")
    parser.add_argument("--cik")
    parser.add_argument("--year", required=True, type=int)
    parser.add_argument("--period", required=True, type=_period)
    parser.add_argument("--window-start")
    parser.add_argument("--window-end")
    parser.add_argument("--company-id")
    parser.add_argument(
        "--filing-type",
        help=(
            "Advanced override. Defaults: Q1/Q3=QUARTERLY_REPORT, "
            "H1=INTERIM_REPORT, FY=ANNUAL_REPORT."
        ),
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ffdf",
        description=(
            "Financial Filing Data Foundation user CLI for official CN/HK filings and gated US SEC development."
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    acquire = sub.add_parser(
        "acquire",
        help="Download/reuse one official filing and register Raw/Registry.",
    )
    _add_filing_arguments(acquire)
    acquire.set_defaults(func=lambda args: _acquire(args)[0])

    ingest = sub.add_parser(
        "ingest",
        help=(
            "Acquire, parse P3-P7, register parsed data, and publish to P8 MCP "
            "catalog when validation is non-blocking."
        ),
    )
    _add_filing_arguments(ingest)
    ingest.set_defaults(func=_ingest)

    status = sub.add_parser(
        "status",
        help="Show Raw/parsed/P8 registration status for one filing period.",
    )
    _add_filing_arguments(status)
    status.set_defaults(func=_status)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except (AcquisitionError, SecError, FileNotFoundError, RuntimeError, ValueError) as exc:
        payload = {
            "command": getattr(args, "command", None),
            "status": "ERROR",
            "error_type": type(exc).__name__,
            "reason_code": getattr(exc, "reason_code", None),
            "message": str(exc),
        }
        _print(payload)
        return 10


if __name__ == "__main__":
    raise SystemExit(main())
