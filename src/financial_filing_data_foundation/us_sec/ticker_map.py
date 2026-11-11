from __future__ import annotations

import hashlib
import json
import base64
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from .errors import P11Reason, SecError
from .identity import normalize_cik, normalize_ticker, resolve_ticker


@dataclass(frozen=True, slots=True)
class TickerMapSnapshot:
    source_url: str
    source_sha256: str
    retrieved_at: str
    mapping: dict[str, tuple[str, ...]]
    source_bytes_b64: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_url": self.source_url,
            "source_sha256": self.source_sha256,
            "retrieved_at": self.retrieved_at,
            "source_bytes_b64": self.source_bytes_b64,
            "mapping": {
                key: list(values) for key, values in sorted(self.mapping.items())
            },
        }

    def verify(self) -> "TickerMapSnapshot":
        """Reparse the authenticated source bytes and verify the derivative."""

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
    return TickerMapSnapshot(
        source_url=source_url,
        source_sha256=hashlib.sha256(bytes(data)).hexdigest(),
        retrieved_at=retrieved_at or datetime.now(timezone.utc).isoformat(),
        mapping=parsed,
        source_bytes_b64=base64.b64encode(bytes(data)).decode("ascii"),
    )


__all__ = ["TickerMapSnapshot", "parse_ticker_map", "snapshot_ticker_map"]
