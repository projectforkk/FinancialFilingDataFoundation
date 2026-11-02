from __future__ import annotations

from pathlib import Path

import pytest

from financial_filing_data_foundation.acquisition import dayu_runner



class _FakeQuery:
    def __init__(
        self,
        *,
        market,
        normalized_ticker,
        start_date,
        end_date,
        target_periods,
    ):
        self.market = market
        self.normalized_ticker = normalized_ticker
        self.start_date = start_date
        self.end_date = end_date
        self.target_periods = target_periods


class _FakeCandidate:
    def __init__(
        self,
        *,
        provider,
        source_id,
        source_url,
        title,
        language,
        filing_date,
        fiscal_year,
        fiscal_period,
        amended,
        content_length,
        etag,
        last_modified,
    ):
        self.provider = provider
        self.source_id = source_id
        self.source_url = source_url
        self.title = title
        self.language = language
        self.filing_date = filing_date
        self.fiscal_year = fiscal_year
        self.fiscal_period = fiscal_period
        self.amended = amended
        self.content_length = content_length
        self.etag = etag
        self.last_modified = last_modified


class _FakeProfile:
    def __init__(self, provider, ticker):
        self.provider = provider
        self.company_id = f"{provider}-company"
        self.company_name = "Example Company"
        self.ticker = ticker


class _FakeAsset:
    def __init__(self, candidate, pdf_path, sha256, content_length):
        self.candidate = candidate
        self.pdf_path = pdf_path
        self.sha256 = sha256
        self.content_length = content_length
        self.downloaded_at = "2026-11-03T00:00:00+00:00"


class _FakeClient:
    provider = "cninfo"
    temp_path: Path | None = None

    def resolve_company(self, query):
        return _FakeProfile(self.provider, query.normalized_ticker)

    def list_report_candidates(self, query, profile):
        return (
            _FakeCandidate(
                provider=self.provider,
                source_id="source-1",
                source_url=(
                    "https://static.cninfo.com.cn/finalpage/test.pdf"
                    if self.provider == "cninfo"
                    else "https://www1.hkexnews.hk/listedco/test.pdf"
                ),
                title="annual report",
                language="zh",
                filing_date="2025-03-01",
                fiscal_year=2024,
                fiscal_period="FY",
                amended=False,
                content_length=123,
                etag=None,
                last_modified=None,
            ),
        )

    def download_report_pdf(self, candidate):
        assert self.temp_path is not None
        self.temp_path.write_bytes(b"%PDF-fake-runner")
        import hashlib

        payload = self.temp_path.read_bytes()
        return _FakeAsset(
            candidate,
            self.temp_path,
            hashlib.sha256(payload).hexdigest(),
            len(payload),
        )


class _FakeCnClient(_FakeClient):
    provider = "cninfo"


class _FakeHkClient(_FakeClient):
    provider = "hkexnews"


def _fake_symbols() -> dict:
    return {
        "CninfoDiscoveryClient": _FakeCnClient,
        "HkexnewsDiscoveryClient": _FakeHkClient,
        "CnReportQuery": _FakeQuery,
        "CnReportCandidate": _FakeCandidate,
    }


@pytest.mark.parametrize(
    ("market", "provider"),
    [("CN", "cninfo"), ("HK", "hkexnews")],
)
def test_discover_contract_with_injected_narrow_client(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    market: str,
    provider: str,
) -> None:
    monkeypatch.setattr(
        dayu_runner,
        "_validate_runtime_request",
        lambda request: (
            request["request_id"],
            tmp_path / "source",
            tmp_path,
            dayu_runner.DAYU_PINNED_COMMIT,
        ),
    )
    monkeypatch.setattr(dayu_runner, "_dayu_symbols", _fake_symbols)

    response = dayu_runner._discover(
        {
            "protocol_version": dayu_runner.PROTOCOL_VERSION,
            "operation": "discover",
            "request_id": "discover-1",
            "dayu_source_dir": str(tmp_path / "source"),
            "market": market,
            "ticker": "600519" if market == "CN" else "00600",
            "window_start": "2025-01-01",
            "window_end": "2025-06-30",
            "target_periods": ["FY"],
        }
    )

    assert response["status"] == "OK"
    assert response["profile"]["provider"] == provider
    assert len(response["candidates"]) == 1
    assert response["candidates"][0]["provider"] == provider
    assert response["candidates"][0]["fiscal_year"] == 2024
    assert response["candidates"][0]["fiscal_period"] == "FY"
    assert response["runner_version"] == "p2-dayu-runner-v1"
    assert response["docling_conversion_used"] is False


def test_download_contract_copies_pdf_and_removes_dayu_temp(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "source"
    source.mkdir()
    staging = tmp_path / "staging.pdf"
    staging.write_bytes(b"")
    dayu_temp = tmp_path / "dayu-temp.pdf"
    _FakeCnClient.temp_path = dayu_temp

    monkeypatch.setattr(
        dayu_runner,
        "_validate_runtime_request",
        lambda request: (
            request["request_id"],
            source,
            tmp_path,
            dayu_runner.DAYU_PINNED_COMMIT,
        ),
    )
    monkeypatch.setattr(dayu_runner, "_dayu_symbols", _fake_symbols)

    candidate = {
        "provider": "cninfo",
        "provider_company_id": "cninfo-company",
        "provider_company_name": "Example Company",
        "ticker": "600519",
        "source_id": "source-1",
        "source_url": "https://static.cninfo.com.cn/finalpage/test.pdf",
        "source_title": "annual report",
        "language": "zh",
        "filing_date": "2025-03-01",
        "fiscal_year": 2024,
        "fiscal_period": "FY",
        "amended": False,
        "remote_content_length": None,
        "etag": None,
        "last_modified": None,
    }

    response = dayu_runner._download(
        {
            "protocol_version": dayu_runner.PROTOCOL_VERSION,
            "operation": "download",
            "request_id": "download-1",
            "dayu_source_dir": str(source),
            "candidate": candidate,
            "staging_path": str(staging),
        }
    )

    assert response["status"] == "OK"
    assert response["candidate"] == candidate
    assert staging.read_bytes() == b"%PDF-fake-runner"
    assert not dayu_temp.exists()
    assert response["runner_version"] == "p2-dayu-runner-v1"
    assert response["docling_conversion_used"] is False
