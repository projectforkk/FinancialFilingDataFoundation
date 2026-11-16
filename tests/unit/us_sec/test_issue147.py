from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from financial_filing_data_foundation.us_sec.errors import P11Reason, SecError
from financial_filing_data_foundation.us_sec.http import SecHttpConfig, SecResponse
from financial_filing_data_foundation.us_sec.path_policy import archive_member_url
from financial_filing_data_foundation.us_sec.ticker_map import (
    TickerMapSnapshot,
    snapshot_ticker_map,
)
from financial_filing_data_foundation.user_cli import (
    _cached_ticker_resolution,
    _parser,
    _persist_ticker_map_snapshot,
    _us_acquire,
    _us_company_and_client,
    _us_ingest,
)


TICKER_MAP_URL = "https://www.sec.gov/files/company_tickers.json"
CIK = "0000320193"
ACCESSION = "0000320193-25-000079"
SUBMISSIONS_URL = f"https://data.sec.gov/submissions/CIK{CIK}.json"
INDEX_URL = archive_member_url(CIK, ACCESSION, "index.json")
PRIMARY_URL = archive_member_url(CIK, ACCESSION, "annual.htm")


def _ticker_map(*rows: tuple[str, int]) -> bytes:
    return json.dumps(
        {
            str(index): {"ticker": ticker, "cik_str": cik}
            for index, (ticker, cik) in enumerate(rows)
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _submissions() -> bytes:
    return json.dumps(
        {
            "cik": CIK,
            "fiscalYearEnd": "0927",
            "filings": {
                "recent": {
                    "accessionNumber": [ACCESSION],
                    "filingDate": ["2025-11-01"],
                    "reportDate": ["2025-09-27"],
                    "form": ["10-K"],
                    "primaryDocument": ["annual.htm"],
                }
            },
        },
        sort_keys=True,
    ).encode("utf-8")


def _primary_html() -> bytes:
    return (
        '<html xmlns:ix="http://www.xbrl.org/2013/inlineXBRL" '
        'xmlns:xbrli="http://www.xbrl.org/2003/instance" '
        'xmlns:us-gaap="http://fasb.org/us-gaap/2025">'
        "<body><ix:header>"
        "<xbrli:context id='c1'><xbrli:entity><xbrli:identifier>0000320193</xbrli:identifier>"
        "</xbrli:entity><xbrli:period><xbrli:instant>2025-09-27</xbrli:instant>"
        "</xbrli:period></xbrli:context>"
        "<xbrli:unit id='USD'><xbrli:measure>iso4217:USD</xbrli:measure></xbrli:unit>"
        "</ix:header><h1>Annual</h1><p>Revenue: "
        "<ix:nonfraction name='us-gaap:Revenues' contextRef='c1' unitRef='USD' decimals='0'>100</ix:nonfraction>"
        "</p></body></html>"
    ).encode("utf-8")


def _args(command: str = "acquire", *, ticker: str = "AAPL") -> object:
    return _parser().parse_args(
        [command, "--market", "US", "--ticker", ticker, "--year", "2025", "--period", "FY"]
    )


def _write_current_observation(root: Path, snapshot: TickerMapSnapshot, payload: dict[str, object] | None = None) -> Path:
    payload = snapshot.to_dict() if payload is None else payload
    snapshot_id = str(payload["snapshot_id"])
    path = root / "workspace" / "ingest" / "us" / "ticker-map" / "observations" / f"{snapshot_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return path


def _patch_online_client(monkeypatch: pytest.MonkeyPatch, root: Path, body: bytes, calls: list[str]) -> None:
    class Client:
        config = SecHttpConfig(contact_email="ops@example.org")

        def fetch(self, url: str, **_: object) -> SecResponse:
            calls.append(url)
            assert url == TICKER_MAP_URL
            return SecResponse(200, {"Content-Type": "application/json"}, body, url)

    monkeypatch.setenv("FFDF_ROOT", str(root))
    monkeypatch.delenv("FFDF_P11_US_DEV", raising=False)
    monkeypatch.setattr(
        "financial_filing_data_foundation.user_cli.SecHttpClient",
        lambda *_args, **_kwargs: Client(),
    )


def _patch_snapshot_times(monkeypatch: pytest.MonkeyPatch, times: list[str]) -> None:
    import financial_filing_data_foundation.user_cli as user_cli

    original = user_cli.snapshot_ticker_map
    values = iter(times)

    def deterministic(data: bytes, *, source_url: str, retrieved_at: str | None = None) -> TickerMapSnapshot:
        return original(data, source_url=source_url, retrieved_at=next(values))

    monkeypatch.setattr(user_cli, "snapshot_ticker_map", deterministic)


def test_t147_01_same_bytes_different_observations_persist_without_source_drift(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    body = _ticker_map(("AAPL", 320193))
    calls: list[str] = []
    _patch_online_client(monkeypatch, tmp_path, body, calls)
    _patch_snapshot_times(monkeypatch, ["2026-11-16T00:00:01+00:00", "2026-11-16T00:00:02+00:00"])

    first, _ = _us_company_and_client(_args(), online=True)
    second, _ = _us_company_and_client(_args(), online=True)

    observation_dir = tmp_path / "workspace" / "ingest" / "us" / "ticker-map" / "observations"
    paths = sorted(observation_dir.glob("*.json"))
    assert first.ticker_source_sha256 == second.ticker_source_sha256
    assert len(paths) == 2
    payloads = [json.loads(path.read_text(encoding="utf-8")) for path in paths]
    assert payloads[0]["source_sha256"] == payloads[1]["source_sha256"]
    assert payloads[0]["snapshot_id"] != payloads[1]["snapshot_id"]
    assert all(TickerMapSnapshot.from_dict(payload).verify() for payload in payloads)
    assert calls == [TICKER_MAP_URL, TICKER_MAP_URL]


def test_t147_02_repeat_online_discovery_continues_after_ticker_persistence(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    body = _ticker_map(("AAPL", 320193))
    calls: list[str] = []
    _patch_online_client(monkeypatch, tmp_path, body, calls)
    _patch_snapshot_times(monkeypatch, ["2026-11-16T00:01:01+00:00", "2026-11-16T00:01:02+00:00"])

    class Client:
        config = SecHttpConfig(contact_email="ops@example.org")

        def fetch(self, url: str, **_: object) -> SecResponse:
            calls.append(url)
            if url == TICKER_MAP_URL:
                return SecResponse(200, {"Content-Type": "application/json"}, body, url)
            if url == SUBMISSIONS_URL:
                return SecResponse(200, {"Content-Type": "application/json"}, _submissions(), url)
            if url == INDEX_URL:
                return SecResponse(
                    200,
                    {"Content-Type": "application/json"},
                    json.dumps({"directory": {"item": [{"name": "annual.htm"}]}}).encode(),
                    url,
                )
            if url == PRIMARY_URL:
                return SecResponse(200, {"Content-Type": "text/html"}, _primary_html(), url)
            raise AssertionError(url)

    monkeypatch.setattr(
        "financial_filing_data_foundation.user_cli.SecHttpClient",
        lambda *_args, **_kwargs: Client(),
    )
    args = _args()

    status, _, _, _, _ = _us_acquire(args, quiet=True)
    assert status == 0
    assert _us_ingest(args) == 0
    assert calls.count(TICKER_MAP_URL) == 2
    assert calls.count(SUBMISSIONS_URL) == 2


def test_t147_03_same_observation_identity_conflict_is_source_drift(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    body = _ticker_map(("AAPL", 320193))
    original = snapshot_ticker_map(body, source_url=TICKER_MAP_URL, retrieved_at="2026-11-16T00:02:01+00:00")
    payload = original.to_dict()
    payload["mapping"] = {"AAPL": ["0000000001"]}
    _write_current_observation(tmp_path, original, payload)
    calls: list[str] = []
    _patch_online_client(monkeypatch, tmp_path, body, calls)
    _patch_snapshot_times(monkeypatch, ["2026-11-16T00:02:01+00:00"])

    with pytest.raises(SecError) as exc_info:
        _us_company_and_client(_args(), online=True)
    assert exc_info.value.reason_code == P11Reason.P11_SOURCE_DRIFT.value


def test_t147_04_legacy_snapshot_is_immutable_and_new_observation_is_separate(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    body = _ticker_map(("AAPL", 320193))
    legacy = snapshot_ticker_map(body, source_url=TICKER_MAP_URL, retrieved_at="2026-11-16T00:03:01+00:00")
    legacy_path = _persist_ticker_map_snapshot(tmp_path, legacy)
    before = hashlib.sha256(legacy_path.read_bytes()).hexdigest()
    calls: list[str] = []
    _patch_online_client(monkeypatch, tmp_path, body, calls)
    _patch_snapshot_times(monkeypatch, ["2026-11-16T00:03:02+00:00"])

    _us_company_and_client(_args(), online=True)

    assert hashlib.sha256(legacy_path.read_bytes()).hexdigest() == before
    observation_dir = tmp_path / "workspace" / "ingest" / "us" / "ticker-map" / "observations"
    assert len(tuple(observation_dir.glob("*.json"))) == 1
    assert tuple((tmp_path / "workspace" / "ingest" / "us" / "ticker-map").glob("*.json")) == (legacy_path,)


def test_t147_05_current_observation_source_bytes_tamper_fails_closed(tmp_path: Path) -> None:
    body = _ticker_map(("AAPL", 320193))
    snapshot = snapshot_ticker_map(body, source_url=TICKER_MAP_URL, retrieved_at="2026-11-16T00:04:01+00:00")
    payload = snapshot.to_dict()
    payload["source_bytes_b64"] = "e30="
    _write_current_observation(tmp_path, snapshot, payload)

    with pytest.raises(SecError) as exc_info:
        _cached_ticker_resolution(tmp_path, "AAPL")
    assert exc_info.value.reason_code == P11Reason.P11_TICKER_SNAPSHOT_INVALID.value


def test_t147_06_current_observation_derivative_tamper_fails_closed(tmp_path: Path) -> None:
    body = _ticker_map(("AAPL", 320193))
    snapshot = snapshot_ticker_map(body, source_url=TICKER_MAP_URL, retrieved_at="2026-11-16T00:05:01+00:00")
    payload = snapshot.to_dict()
    payload["mapping"] = {"AAPL": ["0000000001"]}
    _write_current_observation(tmp_path, snapshot, payload)

    with pytest.raises(SecError) as exc_info:
        _cached_ticker_resolution(tmp_path, "AAPL")
    assert exc_info.value.reason_code == P11Reason.P11_TICKER_SNAPSHOT_INVALID.value


def test_t147_07_newest_verified_snapshot_wins_without_history_merge(tmp_path: Path) -> None:
    first = snapshot_ticker_map(
        _ticker_map(("AAPL", 1)),
        source_url=TICKER_MAP_URL,
        retrieved_at="2026-11-16T00:06:01+00:00",
    )
    second = snapshot_ticker_map(
        _ticker_map(("AAPL", 2)),
        source_url=TICKER_MAP_URL,
        retrieved_at="2026-11-16T00:06:02+00:00",
    )
    _write_current_observation(tmp_path, first)
    _write_current_observation(tmp_path, second)

    result = _cached_ticker_resolution(tmp_path, "AAPL")
    assert result is not None
    assert result[0] == "0000000002"
    assert result[1]["source_sha256"] == second.source_sha256


def test_t147_08_newest_snapshot_missing_ticker_does_not_fall_back_to_legacy(tmp_path: Path) -> None:
    legacy = snapshot_ticker_map(
        _ticker_map(("AAPL", 1)),
        source_url=TICKER_MAP_URL,
        retrieved_at="2026-11-16T00:07:01+00:00",
    )
    _persist_ticker_map_snapshot(tmp_path, legacy)
    newest = snapshot_ticker_map(
        _ticker_map(("MSFT", 2)),
        source_url=TICKER_MAP_URL,
        retrieved_at="2026-11-16T00:07:02+00:00",
    )
    _write_current_observation(tmp_path, newest)

    assert _cached_ticker_resolution(tmp_path, "AAPL") is None


def test_t147_09_explicit_cik_performs_zero_ticker_map_fetches(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("FFDF_ROOT", str(tmp_path))
    monkeypatch.delenv("FFDF_P11_US_DEV", raising=False)
    fetches: list[str] = []

    def forbidden(*_: object, **__: object) -> object:
        fetches.append(TICKER_MAP_URL)
        raise AssertionError("explicit CIK must not construct a ticker-map client")

    monkeypatch.setattr("financial_filing_data_foundation.user_cli.SecHttpClient", forbidden)
    args = _parser().parse_args(
        ["acquire", "--market", "US", "--cik", "320193", "--ticker", "AAPL", "--year", "2025", "--period", "FY"]
    )

    company, client = _us_company_and_client(args, online=True)
    assert company.cik == CIK
    assert client is None
    assert fetches == []


def test_t147_10_formal_ft10_boundary_repeats_without_source_drift(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    body = _ticker_map(("AAPL", 320193))
    calls: list[str] = []
    _patch_online_client(monkeypatch, tmp_path, body, calls)
    _patch_snapshot_times(monkeypatch, ["2026-11-16T00:10:01+00:00", "2026-11-16T00:10:02+00:00"])

    first, _ = _us_company_and_client(_args(), online=True)
    second, second_client = _us_company_and_client(_args(), online=True)

    observations = sorted(
        (tmp_path / "workspace" / "ingest" / "us" / "ticker-map" / "observations").glob("*.json")
    )
    assert second_client is not None
    assert first.cik == CIK == second.cik
    assert first.ticker_source_sha256 == second.ticker_source_sha256
    assert len(observations) == 2
    assert observations[0].stem != observations[1].stem
    assert calls == [TICKER_MAP_URL, TICKER_MAP_URL]
