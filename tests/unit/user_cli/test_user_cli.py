from __future__ import annotations

import json
from pathlib import Path

import pytest

from financial_filing_data_foundation.mcp.catalog import McpCatalog
from financial_filing_data_foundation.user_cli import (
    _CATALOG_FILING_TYPE,
    _IDENTITY_FILING_TYPE,
    _catalog_document,
    _default_window,
    _parser,
    _runtime_paths,
    _upsert_catalog,
)


def test_period_mappings_are_stable() -> None:
    assert _IDENTITY_FILING_TYPE == {
        "Q1": "QUARTERLY_REPORT",
        "H1": "INTERIM_REPORT",
        "Q3": "QUARTERLY_REPORT",
        "FY": "ANNUAL_REPORT",
    }
    assert _CATALOG_FILING_TYPE == {
        "Q1": "Q1",
        "H1": "H1",
        "Q3": "Q3",
        "FY": "ANNUAL",
    }


def test_default_publication_windows() -> None:
    assert _default_window(2024, "Q1") == ("2024-03-01", "2024-05-31")
    assert _default_window(2024, "H1") == ("2024-06-01", "2024-09-30")
    assert _default_window(2024, "Q3") == ("2024-09-01", "2024-11-30")
    assert _default_window(2024, "FY") == ("2025-01-01", "2025-06-30")


def test_cli_parse_exact_requested_shape() -> None:
    args = _parser().parse_args(
        [
            "acquire",
            "--market",
            "CN",
            "--ticker",
            "600519",
            "--year",
            "2026",
            "--period",
            "Q3",
        ]
    )
    assert args.command == "acquire"
    assert args.market == "CN"
    assert args.ticker == "600519"
    assert args.year == 2026
    assert args.period == "Q3"


def test_catalog_upsert_is_idempotent_and_validated(tmp_path: Path) -> None:
    paths = _runtime_paths(tmp_path)
    sha = "a" * 64
    p3 = tmp_path / "workspace" / "ingest" / "cn" / "p3" / sha
    p5 = tmp_path / "workspace" / "ingest" / "cn" / "p5" / sha
    p6 = tmp_path / "workspace" / "ingest" / "cn" / "p6" / sha
    p7 = tmp_path / "workspace" / "ingest" / "cn" / "p7" / sha
    for path in (p3, p5, p6, p7):
        path.mkdir(parents=True)

    class Slot:
        market = "CN"
        fiscal_year = 2026
        raw_fiscal_period = "Q3"

    class Company:
        ticker = "600519"

    class Request:
        slot = Slot()
        company = Company()

    document = _catalog_document(
        tmp_path,
        Request(),
        sha,
        p3,
        p5,
        p6,
        p7,
    )
    assert document["filing_type"] == "Q3"
    assert _upsert_catalog(paths, document, verify_document=False) == "ADDED"
    assert (
        _upsert_catalog(paths, document, verify_document=False)
        == "ALREADY_REGISTERED"
    )

    catalog = McpCatalog.load(tmp_path, paths.catalog)
    assert len(catalog.documents) == 1
    assert catalog.documents[0].document_sha256 == sha

    payload = json.loads(paths.catalog.read_text(encoding="utf-8"))
    assert payload["documents"][0]["ticker"] == "600519"


def test_catalog_refuses_identity_replacement(tmp_path: Path) -> None:
    paths = _runtime_paths(tmp_path)
    base = tmp_path / "workspace" / "ingest" / "cn"
    for sha in ("a" * 64, "b" * 64):
        for stage in ("p3", "p5", "p6", "p7"):
            (base / stage / sha).mkdir(parents=True)

    first = {
        "document_sha256": "a" * 64,
        "market": "CN",
        "ticker": "600519",
        "fiscal_year": 2026,
        "filing_type": "Q3",
        "p3_artifact_dir": f"workspace/ingest/cn/p3/{'a' * 64}",
        "p5_artifact_dir": f"workspace/ingest/cn/p5/{'a' * 64}",
        "p6_artifact_dir": f"workspace/ingest/cn/p6/{'a' * 64}",
        "p7_artifact_dir": f"workspace/ingest/cn/p7/{'a' * 64}",
    }
    second = dict(first)
    second["document_sha256"] = "b" * 64
    for stage in ("p3", "p5", "p6", "p7"):
        second[f"{stage}_artifact_dir"] = (
            f"workspace/ingest/cn/{stage}/{'b' * 64}"
        )

    assert _upsert_catalog(paths, first, verify_document=False) == "ADDED"
    with pytest.raises(RuntimeError, match="different SHA"):
        _upsert_catalog(paths, second, verify_document=False)
