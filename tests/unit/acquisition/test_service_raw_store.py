from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pymupdf
import pytest

from financial_filing_data_foundation.acquisition.models import (
    AcquisitionCandidate,
    AcquisitionError,
    AcquisitionReason,
    AcquisitionRequest,
    AcquisitionStatus,
    DiscoveryResult,
    ProviderCompanyProfile,
    RunnerDownloadedAsset,
)
from financial_filing_data_foundation.acquisition.raw_store import (
    RawDocumentStore,
    sha256_file,
)
from financial_filing_data_foundation.acquisition.service import acquire_slot
from financial_filing_data_foundation.identity import (
    CompanyRef,
    FilingIdentity,
    FilingSlotKey,
    SourceMetadata,
)
from financial_filing_data_foundation.registry import SQLiteRegistry


def _company(market: str = "CN", ticker: str = "600519") -> CompanyRef:
    return CompanyRef(market, f"{market}:{ticker}", ticker)


def _slot(
    market: str = "CN",
    ticker: str = "600519",
    year: int = 2024,
    period: str = "FY",
) -> FilingSlotKey:
    return FilingSlotKey(
        market,
        f"{market}:{ticker}",
        "ANNUAL_REPORT",
        year,
        period,
    )


def _request(
    market: str = "CN",
    ticker: str = "600519",
    year: int = 2024,
    period: str = "FY",
) -> AcquisitionRequest:
    return AcquisitionRequest(
        company=_company(market, ticker),
        slot=_slot(market, ticker, year, period),
        window_start="2025-01-01",
        window_end="2025-06-30",
    )


def _candidate(
    *,
    market: str = "CN",
    ticker: str = "600519",
    year: int = 2024,
    period: str = "FY",
    source_id: str = "source-1",
    url: str | None = None,
) -> AcquisitionCandidate:
    provider = "cninfo" if market == "CN" else "hkexnews"
    if url is None:
        url = (
            "https://static.cninfo.com.cn/finalpage/test.pdf"
            if market == "CN"
            else "https://www1.hkexnews.hk/listedco/test.pdf"
        )
    return AcquisitionCandidate(
        provider=provider,
        provider_company_id=f"{provider}-company",
        provider_company_name="Example Company",
        ticker=ticker,
        source_id=source_id,
        source_url=url,
        source_title="2024 annual report",
        language="zh",
        filing_date="2025-03-01",
        fiscal_year=year,
        fiscal_period=period,
        amended=False,
        remote_content_length=None,
        etag=None,
        last_modified=None,
    )


def _make_pdf(path: Path, text: str = "official filing") -> None:
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((72, 72), text)
    doc.save(path)
    doc.close()


class FakeProvider:
    def __init__(
        self,
        request: AcquisitionRequest,
        candidates: tuple[AcquisitionCandidate, ...],
        *,
        bad_sha: bool = False,
    ) -> None:
        provider = "cninfo" if request.slot.market == "CN" else "hkexnews"
        self.name = provider
        self.runtime = None
        self.profile = ProviderCompanyProfile(
            provider=provider,
            company_id=f"{provider}-company",
            company_name="Example Company",
            ticker=request.company.ticker,
        )
        self.candidates = candidates
        self.bad_sha = bad_sha
        self.discover_calls = 0
        self.download_calls = 0

    def discover_documents(self, request: AcquisitionRequest) -> DiscoveryResult:
        self.discover_calls += 1
        return DiscoveryResult(self.profile, self.candidates)

    def download_document(
        self,
        candidate: AcquisitionCandidate,
        staging_path: Path,
    ) -> RunnerDownloadedAsset:
        self.download_calls += 1
        _make_pdf(staging_path)
        actual_sha = sha256_file(staging_path)
        return RunnerDownloadedAsset(
            candidate=candidate,
            staging_path=staging_path.resolve(),
            sha256=("0" * 64 if self.bad_sha else actual_sha),
            content_length=staging_path.stat().st_size,
            downloaded_at="2026-11-03T00:00:00+00:00",
        )

    def source_metadata(
        self,
        candidate: AcquisitionCandidate,
        downloaded_at: str,
    ) -> SourceMetadata:
        return SourceMetadata(
            provider=candidate.provider,
            source_id=candidate.source_id,
            source_url=candidate.source_url,
            source_title=candidate.source_title,
            filing_date=candidate.filing_date,
            provider_company_id=candidate.provider_company_id,
            acquired_at=downloaded_at,
        )


def test_request_requires_matching_company_and_slot() -> None:
    with pytest.raises(ValueError, match="company.market"):
        AcquisitionRequest(
            company=_company("CN", "600519"),
            slot=_slot("HK", "00600"),
            window_start="2025-01-01",
            window_end="2025-06-30",
        )


def test_request_requires_ordered_date_window() -> None:
    with pytest.raises(ValueError, match="window_start"):
        AcquisitionRequest(
            company=_company(),
            slot=_slot(),
            window_start="2025-06-30",
            window_end="2025-01-01",
        )


def test_raw_store_validates_commits_and_deduplicates(tmp_path: Path) -> None:
    store = RawDocumentStore(tmp_path / "raw")
    first = store.new_staging_path()
    _make_pdf(first, "same")
    sha = sha256_file(first)
    size = first.stat().st_size

    actual_sha, actual_size = store.validate_staging_pdf(
        first,
        expected_sha256=sha,
        expected_size=size,
    )
    stored = store.commit_staging(first, actual_sha)

    assert actual_size == size
    assert stored.document_sha256 == sha
    assert stored.path.exists()
    assert stored.reused_existing is False

    second = store.new_staging_path()
    second.write_bytes(stored.path.read_bytes())
    assert sha256_file(second) == sha
    stored_again = store.commit_staging(second, sha)

    assert stored_again.path == stored.path
    assert stored_again.reused_existing is True
    assert not second.exists()


def test_raw_store_rejects_non_pdf_and_sha_mismatch(tmp_path: Path) -> None:
    store = RawDocumentStore(tmp_path / "raw")
    staging = store.new_staging_path()
    staging.write_bytes(b"not-a-pdf")

    with pytest.raises(AcquisitionError) as exc_info:
        store.validate_staging_pdf(staging)
    assert exc_info.value.reason_code == AcquisitionReason.PDF_VALIDATION_FAILED.value

    staging.write_bytes(b"%PDF-fake")
    with pytest.raises(AcquisitionError) as exc_info:
        store.validate_staging_pdf(staging, expected_sha256="0" * 64)
    assert exc_info.value.reason_code == AcquisitionReason.SHA_MISMATCH.value


def test_raw_store_detects_existing_object_corruption(tmp_path: Path) -> None:
    store = RawDocumentStore(tmp_path / "raw")
    staging = store.new_staging_path()
    _make_pdf(staging, "valid")
    sha = sha256_file(staging)
    final = store.sha_root / sha[:2] / f"{sha}.pdf"
    final.parent.mkdir(parents=True, exist_ok=True)
    final.write_bytes(b"corrupt")

    with pytest.raises(AcquisitionError) as exc_info:
        store.commit_staging(staging, sha)
    assert exc_info.value.reason_code == AcquisitionReason.RAW_STORE_CORRUPTION.value


def test_receipt_id_is_deterministic_and_semantic_collision_blocks(
    tmp_path: Path,
) -> None:
    store = RawDocumentStore(tmp_path / "raw")
    payload = {
        "provider": "cninfo",
        "source_id": "source-1",
        "document_sha256": "a" * 64,
        "value": 1,
    }
    first = store.write_receipt(payload)
    second = store.write_receipt(payload)
    assert first == second

    changed = dict(payload)
    changed["value"] = 2
    with pytest.raises(AcquisitionError):
        store.write_receipt(changed)


def test_service_cn_success_registers_raw_provenance_and_receipt(
    tmp_path: Path,
) -> None:
    request = _request()
    candidate = _candidate()
    provider = FakeProvider(request, (candidate,))
    store = RawDocumentStore(tmp_path / "raw")
    registry = SQLiteRegistry(tmp_path / "registry.sqlite")

    result = acquire_slot(request, provider, store, registry)

    assert result.status == AcquisitionStatus.DOWNLOADED
    assert result.reason_code == AcquisitionReason.ACQUISITION_COMPLETE.value
    assert result.raw_path is not None and result.raw_path.exists()
    assert result.receipt_path is not None and result.receipt_path.exists()
    assert provider.discover_calls == 1
    assert provider.download_calls == 1

    local = registry.resolve_local_document(request.slot)
    assert local.document_sha256 == result.document_sha256
    assert local.canonical_path == result.raw_path

    sources = registry.list_document_sources(result.document_sha256 or "")
    assert len(sources) == 1
    assert sources[0].provider == "cninfo"
    assert sources[0].source_id == "source-1"

    receipt = json.loads(result.receipt_path.read_text(encoding="utf-8"))
    assert receipt["docling_conversion_used"] is False
    assert receipt["ffdf_recomputed_sha256"] == result.document_sha256
    assert receipt["registry_result"]["document_sha256"] == result.document_sha256


def test_service_hk_success(tmp_path: Path) -> None:
    request = _request("HK", "00600")
    candidate = _candidate(market="HK", ticker="00600")
    provider = FakeProvider(request, (candidate,))
    result = acquire_slot(
        request,
        provider,
        RawDocumentStore(tmp_path / "raw"),
        SQLiteRegistry(tmp_path / "registry.sqlite"),
    )

    assert result.status == AcquisitionStatus.DOWNLOADED
    assert result.provider == "hkexnews"


def test_service_second_run_short_circuits_without_provider_calls(
    tmp_path: Path,
) -> None:
    request = _request()
    candidate = _candidate()
    provider = FakeProvider(request, (candidate,))
    store = RawDocumentStore(tmp_path / "raw")
    registry = SQLiteRegistry(tmp_path / "registry.sqlite")

    first = acquire_slot(request, provider, store, registry)
    assert first.status == AcquisitionStatus.DOWNLOADED
    calls = (provider.discover_calls, provider.download_calls)

    second = acquire_slot(request, provider, store, registry)
    assert second.status == AcquisitionStatus.REUSED_LOCAL
    assert (provider.discover_calls, provider.download_calls) == calls
    assert second.document_sha256 == first.document_sha256
    assert second.raw_path == first.raw_path


def test_service_no_candidate_does_not_download(tmp_path: Path) -> None:
    request = _request()
    provider = FakeProvider(request, ())
    result = acquire_slot(
        request,
        provider,
        RawDocumentStore(tmp_path / "raw"),
        SQLiteRegistry(tmp_path / "registry.sqlite"),
    )

    assert result.status == AcquisitionStatus.NOT_FOUND
    assert provider.download_calls == 0


def test_service_ambiguous_candidates_require_review(tmp_path: Path) -> None:
    request = _request()
    provider = FakeProvider(
        request,
        (
            _candidate(source_id="one"),
            _candidate(
                source_id="two",
                url="https://static.cninfo.com.cn/finalpage/two.pdf",
            ),
        ),
    )
    result = acquire_slot(
        request,
        provider,
        RawDocumentStore(tmp_path / "raw"),
        SQLiteRegistry(tmp_path / "registry.sqlite"),
    )

    assert result.status == AcquisitionStatus.REVIEW_REQUIRED
    assert (
        result.reason_code
        == AcquisitionReason.ACQUISITION_CANDIDATE_AMBIGUOUS.value
    )
    assert provider.download_calls == 0


def test_service_filters_wrong_year_to_not_found(tmp_path: Path) -> None:
    request = _request(year=2024)
    provider = FakeProvider(request, (_candidate(year=2023),))
    result = acquire_slot(
        request,
        provider,
        RawDocumentStore(tmp_path / "raw"),
        SQLiteRegistry(tmp_path / "registry.sqlite"),
    )
    assert result.status == AcquisitionStatus.NOT_FOUND
    assert provider.download_calls == 0


def test_service_rejects_unapproved_source_host_before_download(
    tmp_path: Path,
) -> None:
    request = _request()
    provider = FakeProvider(
        request,
        (_candidate(url="https://example.com/fake.pdf"),),
    )
    with pytest.raises(AcquisitionError) as exc_info:
        acquire_slot(
            request,
            provider,
            RawDocumentStore(tmp_path / "raw"),
            SQLiteRegistry(tmp_path / "registry.sqlite"),
        )
    assert exc_info.value.reason_code == AcquisitionReason.SOURCE_HOST_NOT_ALLOWED.value
    assert provider.download_calls == 0


def test_service_rejects_hk_http_source(tmp_path: Path) -> None:
    request = _request("HK", "00600")
    provider = FakeProvider(
        request,
        (
            _candidate(
                market="HK",
                ticker="00600",
                url="http://www1.hkexnews.hk/listedco/test.pdf",
            ),
        ),
    )
    with pytest.raises(AcquisitionError) as exc_info:
        acquire_slot(
            request,
            provider,
            RawDocumentStore(tmp_path / "raw"),
            SQLiteRegistry(tmp_path / "registry.sqlite"),
        )
    assert exc_info.value.reason_code == AcquisitionReason.SOURCE_HOST_NOT_ALLOWED.value


def test_service_rejects_runner_sha_mismatch_and_does_not_register(
    tmp_path: Path,
) -> None:
    request = _request()
    provider = FakeProvider(request, (_candidate(),), bad_sha=True)
    registry = SQLiteRegistry(tmp_path / "registry.sqlite")

    with pytest.raises(AcquisitionError) as exc_info:
        acquire_slot(
            request,
            provider,
            RawDocumentStore(tmp_path / "raw"),
            registry,
        )

    assert exc_info.value.reason_code == AcquisitionReason.SHA_MISMATCH.value
    assert registry.count_documents() == 0


def test_service_local_ambiguous_short_circuits_without_discovery(
    tmp_path: Path,
) -> None:
    request = _request()
    registry = SQLiteRegistry(tmp_path / "registry.sqlite")
    a = tmp_path / "a.pdf"
    b = tmp_path / "b.pdf"
    _make_pdf(a, "a")
    _make_pdf(b, "b")
    registry.register_document(a, expected_identity=FilingIdentity(request.slot))
    registry.register_document(b, expected_identity=FilingIdentity(request.slot))
    provider = FakeProvider(request, (_candidate(),))

    result = acquire_slot(
        request,
        provider,
        RawDocumentStore(tmp_path / "raw"),
        registry,
    )

    assert result.status == AcquisitionStatus.REVIEW_REQUIRED
    assert provider.discover_calls == 0
    assert provider.download_calls == 0
