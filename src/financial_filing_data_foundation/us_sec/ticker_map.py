from __future__ import annotations

import hashlib
import json
import base64
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from .errors import P11Reason, SecError
from .identity import normalize_cik, normalize_ticker, resolve_ticker


SEC_TICKER_MAP_URL = "https://www.sec.gov/files/company_tickers.json"


def normalize_retrieved_at(value: str) -> str:
    """Return a timezone-aware UTC ISO-8601 representation."""

    if not isinstance(value, str) or not value.strip():
        raise SecError(
            P11Reason.P11_TICKER_SNAPSHOT_INVALID,
            "ticker snapshot retrieved_at must be a non-empty string",
        )
    text = value.strip()
    if text.endswith(("Z", "z")):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise SecError(
            P11Reason.P11_TICKER_SNAPSHOT_INVALID,
            "ticker snapshot retrieved_at is not valid ISO-8601",
        ) from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise SecError(
            P11Reason.P11_TICKER_SNAPSHOT_INVALID,
            "ticker snapshot retrieved_at must be timezone-aware",
        )
    return parsed.astimezone(timezone.utc).isoformat()


def compute_ticker_snapshot_id(
    *,
    source_url: str,
    source_sha256: str,
    retrieved_at: str,
) -> str:
    """Compute the immutable identity of one ticker-map retrieval observation."""

    canonical = json.dumps(
        {
            "source_sha256": str(source_sha256).strip().lower(),
            "source_url": str(source_url),
            "retrieved_at": normalize_retrieved_at(retrieved_at),
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


@dataclass(frozen=True, slots=True)
class TickerMapSnapshot:
    source_url: str
    source_sha256: str
    retrieved_at: str
    mapping: dict[str, tuple[str, ...]]
    source_bytes_b64: str | None = None
    snapshot_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        snapshot_id = self.snapshot_id or compute_ticker_snapshot_id(
            source_url=self.source_url,
            source_sha256=self.source_sha256,
            retrieved_at=self.retrieved_at,
        )
        return {
            "snapshot_id": snapshot_id,
            "source_url": self.source_url,
            "source_sha256": str(self.source_sha256).lower(),
            "retrieved_at": self.retrieved_at,
            "source_bytes_b64": self.source_bytes_b64,
            "mapping": {
                key: list(values) for key, values in sorted(self.mapping.items())
            },
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "TickerMapSnapshot":
        if not isinstance(payload, dict):
            raise SecError(P11Reason.P11_TICKER_SNAPSHOT_INVALID, "ticker snapshot payload is invalid")
        source_url = payload.get("source_url")
        source_sha256 = payload.get("source_sha256")
        retrieved_at = payload.get("retrieved_at")
        source_bytes_b64 = payload.get("source_bytes_b64")
        raw_mapping = payload.get("mapping")
        snapshot_id = payload.get("snapshot_id")
        if not isinstance(source_url, str) or not source_url.strip():
            raise SecError(P11Reason.P11_TICKER_SNAPSHOT_INVALID, "ticker snapshot source URL is invalid")
        if not isinstance(source_sha256, str) or not source_sha256.strip():
            raise SecError(P11Reason.P11_TICKER_SNAPSHOT_INVALID, "ticker snapshot source SHA is invalid")
        if not isinstance(retrieved_at, str):
            raise SecError(P11Reason.P11_TICKER_SNAPSHOT_INVALID, "ticker snapshot retrieved_at is invalid")
        if source_bytes_b64 is not None and not isinstance(source_bytes_b64, str):
            raise SecError(P11Reason.P11_TICKER_SNAPSHOT_INVALID, "ticker snapshot source bytes are invalid")
        if snapshot_id is not None and (not isinstance(snapshot_id, str) or not snapshot_id.strip()):
            raise SecError(P11Reason.P11_TICKER_SNAPSHOT_INVALID, "ticker snapshot ID is invalid")
        if not isinstance(raw_mapping, dict):
            raise SecError(P11Reason.P11_TICKER_SNAPSHOT_INVALID, "ticker snapshot mapping is invalid")
        mapping: dict[str, tuple[str, ...]] = {}
        try:
            for raw_ticker, raw_values in raw_mapping.items():
                normalized_ticker = normalize_ticker(str(raw_ticker))
                values = [raw_values] if isinstance(raw_values, str) else raw_values
                if not isinstance(values, list):
                    raise ValueError(normalized_ticker)
                normalized_values = tuple(
                    sorted({normalize_cik(str(value)) for value in values})
                )
                mapping[normalized_ticker] = normalized_values
        except (SecError, TypeError, ValueError) as exc:
            raise SecError(P11Reason.P11_TICKER_SNAPSHOT_INVALID, "ticker snapshot mapping is invalid") from exc
        return cls(
            source_url=source_url,
            source_sha256=source_sha256.strip().lower(),
            retrieved_at=retrieved_at,
            mapping=mapping,
            source_bytes_b64=source_bytes_b64,
            snapshot_id=snapshot_id.strip().lower() if isinstance(snapshot_id, str) else None,
        )

    def verify(self) -> "TickerMapSnapshot":
        """Reparse the authenticated source bytes and verify the derivative."""

        if self.source_url != SEC_TICKER_MAP_URL:
            raise SecError(P11Reason.P11_TICKER_SNAPSHOT_INVALID, "ticker snapshot source URL is not official")
        normalized_retrieved_at = normalize_retrieved_at(self.retrieved_at)
        expected_snapshot_id = compute_ticker_snapshot_id(
            source_url=self.source_url,
            source_sha256=self.source_sha256,
            retrieved_at=normalized_retrieved_at,
        )
        if self.snapshot_id is not None and self.snapshot_id.lower() != expected_snapshot_id:
            raise SecError(P11Reason.P11_TICKER_SNAPSHOT_INVALID, "ticker snapshot ID mismatch")
        if not self.source_bytes_b64:
            raise SecError(P11Reason.P11_TICKER_SNAPSHOT_INVALID, "ticker snapshot source bytes are missing")
        try:
            source_bytes = base64.b64decode(self.source_bytes_b64, validate=True)
        except (ValueError, TypeError) as exc:
            raise SecError(P11Reason.P11_TICKER_SNAPSHOT_INVALID, "ticker snapshot source bytes are invalid") from exc
        actual_sha = hashlib.sha256(source_bytes).hexdigest()
        if actual_sha != str(self.source_sha256).lower():
            raise SecError(P11Reason.P11_TICKER_SNAPSHOT_INVALID, "ticker snapshot source bytes hash mismatch")
        try:
            reparsed = parse_ticker_map(source_bytes)
        except SecError as exc:
            raise SecError(P11Reason.P11_TICKER_SNAPSHOT_INVALID, "ticker snapshot source bytes cannot be parsed") from exc
        if not isinstance(reparsed, dict):
            raise SecError(P11Reason.P11_TICKER_SNAPSHOT_INVALID, "ticker snapshot mapping is invalid")
        normalized = {key: tuple(value) for key, value in reparsed.items()}
        if normalized != self.mapping:
            raise SecError(P11Reason.P11_TICKER_SNAPSHOT_INVALID, "ticker snapshot mapping derivative mismatch")
        return self


def parse_ticker_map(data: bytes, ticker: str | None = None) -> dict[str, tuple[str, ...]] | str:
    if not isinstance(data, (bytes, bytearray)):
        raise SecError(P11Reason.P11_SEC_DISCOVERY_FAILED, "ticker map must be bytes")
    try:
        payload = json.loads(bytes(data).decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SecError(P11Reason.P11_SEC_DISCOVERY_FAILED, "SEC ticker map is invalid JSON") from exc
    if not isinstance(payload, dict):
        raise SecError(P11Reason.P11_SEC_DISCOVERY_FAILED, "SEC ticker map must be an object")

    mapping: dict[str, set[str]] = {}
    for raw in payload.values():
        if not isinstance(raw, dict):
            continue
        raw_ticker = raw.get("ticker")
        raw_cik = raw.get("cik_str")
        if not isinstance(raw_ticker, str) or not raw_ticker.strip():
            continue
        try:
            normalized_ticker = normalize_ticker(raw_ticker)
            normalized_cik = normalize_cik(str(raw_cik))
        except (SecError, ValueError):
            continue
        mapping.setdefault(normalized_ticker, set()).add(normalized_cik)

    result = {key: tuple(sorted(values)) for key, values in sorted(mapping.items())}
    if ticker is not None:
        return resolve_ticker(ticker, result)
    return result


def snapshot_ticker_map(
    data: bytes,
    *,
    source_url: str,
    retrieved_at: str | None = None,
) -> TickerMapSnapshot:
    parsed = parse_ticker_map(data)
    assert isinstance(parsed, dict)
    source_sha256 = hashlib.sha256(bytes(data)).hexdigest()
    normalized_retrieved_at = normalize_retrieved_at(
        retrieved_at or datetime.now(timezone.utc).isoformat()
    )
    return TickerMapSnapshot(
        source_url=source_url,
        source_sha256=source_sha256,
        retrieved_at=normalized_retrieved_at,
        mapping=parsed,
        source_bytes_b64=base64.b64encode(bytes(data)).decode("ascii"),
        snapshot_id=compute_ticker_snapshot_id(
            source_url=source_url,
            source_sha256=source_sha256,
            retrieved_at=normalized_retrieved_at,
        ),
    )


__all__ = [
    "SEC_TICKER_MAP_URL",
    "TickerMapSnapshot",
    "compute_ticker_snapshot_id",
    "normalize_retrieved_at",
    "parse_ticker_map",
    "snapshot_ticker_map",
]
