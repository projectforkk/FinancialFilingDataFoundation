from __future__ import annotations

from collections.abc import Mapping, Sequence

from .errors import P11Reason, SecError
from .models import SecCompanyRef


def normalize_cik(value: str) -> str:
    raw = value.strip().upper()
    if raw.startswith("CIK"):
        raw = raw[3:]
    if not raw.isascii() or not raw.isdigit() or not 1 <= len(raw) <= 10:
        raise SecError(P11Reason.P11_INVALID_US_IDENTITY, "CIK must contain 1-10 digits")
    return raw.zfill(10)


def normalize_ticker(value: str) -> str:
    raw = value.strip().upper()
    if not raw or not raw.isascii() or any(ch.isspace() for ch in raw):
        raise SecError(P11Reason.P11_INVALID_US_IDENTITY, "ticker must be a non-empty ASCII alias")
    return raw


def resolve_ticker(
    ticker: str,
    mapping: Mapping[str, str | Sequence[str]],
) -> str:
    normalized = normalize_ticker(ticker)
    raw = mapping.get(normalized)
    if raw is None:
        raw = mapping.get(normalized.casefold())
    if raw is None:
        raise SecError(P11Reason.P11_INVALID_US_IDENTITY, f"ticker not found: {normalized}")
    values = [raw] if isinstance(raw, str) else list(raw)
    ciks = tuple(sorted({normalize_cik(item) for item in values}))
    if len(ciks) != 1:
        raise SecError(
            P11Reason.P11_TICKER_CIK_AMBIGUOUS,
            f"ticker maps to multiple CIKs: {normalized}",
        )
    return ciks[0]


def sec_company(
    *,
    cik: str,
    ticker: str | None,
    company_name: str | None = None,
    allow_development: bool = False,
    ticker_source_url: str | None = None,
    ticker_source_sha256: str | None = None,
    ticker_retrieved_at: str | None = None,
) -> SecCompanyRef:
    from .feature_gate import require_us_development

    require_us_development(allow_development)
    normalized_cik = normalize_cik(cik)
    alias = normalize_ticker(ticker) if ticker else f"CIK{normalized_cik}"
    return SecCompanyRef(
        cik=normalized_cik,
        ticker=alias,
        company_id=f"US:CIK{normalized_cik}",
        company_name=company_name.strip() if company_name else None,
        ticker_source_url=ticker_source_url,
        ticker_source_sha256=ticker_source_sha256,
        ticker_retrieved_at=ticker_retrieved_at,
    )
