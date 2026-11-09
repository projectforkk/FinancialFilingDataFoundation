from __future__ import annotations

import pytest

from financial_filing_data_foundation.identity import SUPPORTED_MARKETS
from financial_filing_data_foundation.us_sec.errors import P11Reason, SecError
from financial_filing_data_foundation.us_sec.feature_gate import (
    is_us_development_enabled,
    require_us_development,
)
from financial_filing_data_foundation.us_sec.identity import (
    normalize_cik,
    normalize_ticker,
    resolve_ticker,
    sec_company,
)
from financial_filing_data_foundation.us_sec.models import SecIssuerKind, SecFilingSlot
from financial_filing_data_foundation.us_sec.policy import SecFormPolicy


def test_us_is_not_added_to_accepted_market_tuple() -> None:
    assert SUPPORTED_MARKETS == ("CN", "HK")


def test_cik_and_ticker_normalize_without_company_name_guessing() -> None:
    assert normalize_cik("320193") == "0000320193"
    assert normalize_cik("CIK0000320193") == "0000320193"
    assert normalize_ticker(" aapl ") == "AAPL"
    with pytest.raises(SecError) as exc_info:
        normalize_cik("Apple")
    assert exc_info.value.reason_code == P11Reason.P11_INVALID_US_IDENTITY.value


def test_explicit_cik_builds_stable_company_identity() -> None:
    company = sec_company(cik="320193", ticker=None, allow_development=True)
    assert company.cik == "0000320193"
    assert company.company_id == "US:CIK0000320193"
    assert company.ticker == "CIK0000320193"


def test_ambiguous_exact_ticker_fails_closed() -> None:
    with pytest.raises(SecError) as exc_info:
        resolve_ticker("DUP", {"DUP": ("0000000001", "0000000002")})
    assert exc_info.value.reason_code == P11Reason.P11_TICKER_CIK_AMBIGUOUS.value


def test_domestic_period_policy_includes_q2() -> None:
    assert SecFormPolicy.forms_for("Q1", SecIssuerKind.DOMESTIC) == ("10-Q",)
    assert SecFormPolicy.forms_for("Q2", SecIssuerKind.DOMESTIC) == ("10-Q",)
    assert SecFormPolicy.forms_for("Q3", SecIssuerKind.DOMESTIC) == ("10-Q",)
    assert SecFormPolicy.forms_for("FY", SecIssuerKind.DOMESTIC) == ("10-K",)


def test_fpi_annual_is_supported_but_quarterly_6k_is_not_assumed() -> None:
    assert SecFormPolicy.forms_for("FY", SecIssuerKind.FPI) == ("20-F", "40-F")
    with pytest.raises(SecError) as exc_info:
        SecFormPolicy.forms_for("Q2", SecIssuerKind.FPI)
    assert (
        exc_info.value.reason_code
        == P11Reason.P11_UNSUPPORTED_FPI_PERIODIC_MAPPING.value
    )


def test_feature_gate_is_explicit_and_default_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("FFDF_P11_US_DEV", raising=False)
    assert is_us_development_enabled() is False
    with pytest.raises(SecError) as exc_info:
        require_us_development()
    assert exc_info.value.reason_code == P11Reason.P11_INVALID_US_IDENTITY.value
    monkeypatch.setenv("FFDF_P11_US_DEV", "1")
    assert is_us_development_enabled() is True
    require_us_development()


def test_sec_filing_slot_serialization_is_stable() -> None:
    slot = SecFilingSlot(
        company_id="US:CIK0000320193",
        fiscal_year=2024,
        raw_fiscal_period="Q2",
        issuer_kind=SecIssuerKind.DOMESTIC,
    )
    assert slot.serialize() == "US|US:CIK0000320193|SEC|2024|Q2"
