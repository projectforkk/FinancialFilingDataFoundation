import pytest

from financial_filing_data_foundation.identity import (
    CompanyRef,
    FilingPolicy,
    FilingRequirement,
    FilingSlotKey,
    SupplementalFilingIdentity,
    accession_number_without_dashes,
    normalize_accession_number,
    normalize_cik,
    normalize_sec_form,
    resolve_us_company_identity,
)
from financial_filing_data_foundation.identity.sec import (
    CikInvalid,
    CompanyIdentityAmbiguous,
    CompanyIdentityNotFound,
)


def test_p11c_01_cn_hk_still_require_non_empty_ticker() -> None:
    assert CompanyRef("cn", "CN:600519", " 600519 ").ticker == "600519"
    assert CompanyRef("hk", "HK:00005", " 00005 ").ticker == "00005"
    with pytest.raises(ValueError, match="ticker must not be empty"):
        CompanyRef("CN", "CN:600519", "")
    with pytest.raises(ValueError, match="ticker must not be empty"):
        CompanyRef("HK", "HK:00005", "   ")


def test_p11c_02_us_company_ref_zero_pads_cik_and_allows_null_ticker() -> None:
    company = CompanyRef("us", "320193", None)
    assert company.market == "US"
    assert company.company_id == "0000320193"
    assert company.ticker is None


def test_p11c_03_us_cik_only_resolution_does_not_fabricate_ticker() -> None:
    resolved = resolve_us_company_identity(cik="320193", ticker=None)
    assert resolved.cik == "0000320193"
    assert resolved.ticker is None


def test_p11c_04_one_submission_ticker_populates_display_ticker() -> None:
    resolved = resolve_us_company_identity(cik="320193", ticker=None, submission_tickers=(" aapl ",))
    assert resolved.ticker == "AAPL"


def test_p11c_05_multiple_submission_tickers_leave_display_ticker_null() -> None:
    resolved = resolve_us_company_identity(cik="320193", ticker=None, submission_tickers=("AAPL", "APC"))
    assert resolved.ticker is None


def test_p11c_06_ticker_only_zero_match_is_not_found() -> None:
    with pytest.raises(CompanyIdentityNotFound) as exc_info:
        resolve_us_company_identity(cik=None, ticker="AAPL", official_ticker_rows=(("MSFT", "789019"),))
    assert exc_info.value.reason_code == "P11_COMPANY_IDENTITY_NOT_FOUND"


def test_p11c_07_ticker_only_multiple_cik_match_is_ambiguous() -> None:
    with pytest.raises(CompanyIdentityAmbiguous) as exc_info:
        resolve_us_company_identity(cik=None, ticker="ABC", official_ticker_rows=(("ABC", "1"), ("abc", "2")))
    assert exc_info.value.reason_code == "P11_COMPANY_IDENTITY_AMBIGUOUS"


def test_p11c_08_caller_ticker_cik_mismatch_is_ambiguous() -> None:
    with pytest.raises(CompanyIdentityAmbiguous) as exc_info:
        resolve_us_company_identity(cik="320193", ticker="MSFT", official_ticker_rows=(("MSFT", "789019"),))
    assert exc_info.value.reason_code == "P11_COMPANY_IDENTITY_AMBIGUOUS"


@pytest.mark.parametrize("bad", ["0", "-1", "+1", "1.0", "1,000", "12345678901", "１２３", "12 34", ""])
def test_p11c_09_invalid_cik_is_rejected_with_reason_code(bad: str) -> None:
    with pytest.raises(CikInvalid) as exc_info:
        normalize_cik(bad)
    assert exc_info.value.reason_code == "P11_CIK_INVALID"
    assert normalize_cik(" 320193 ") == "0000320193"


def test_p11c_10_us_q2_is_valid() -> None:
    slot = FilingSlotKey("US", "320193", "10-Q", 2025, "Q2")
    assert slot.serialize() == "US|0000320193|10-Q|2025|Q2"


def test_p11c_11_cn_q2_is_rejected() -> None:
    with pytest.raises(ValueError, match="unsupported P1 fiscal period"):
        FilingSlotKey("CN", "company-1", "QUARTERLY_REPORT", 2025, "Q2")
    with pytest.raises(ValueError, match="unsupported P1 fiscal period"):
        FilingRequirement("QUARTERLY_REPORT", "Q2")


def test_p11c_12_hk_q2_is_rejected() -> None:
    with pytest.raises(ValueError, match="unsupported P1 fiscal period"):
        FilingSlotKey("HK", "company-1", "INTERIM_REPORT", 2025, "Q2")


def test_p11c_13_h1_remains_valid_for_existing_markets() -> None:
    assert FilingSlotKey("CN", "company-1", "INTERIM_REPORT", 2025, "H1").raw_fiscal_period == "H1"
    assert FilingSlotKey("HK", "company-2", "INTERIM_REPORT", 2025, "H1").raw_fiscal_period == "H1"


@pytest.mark.parametrize(("raw", "base"), [("10-K/A", "10-K"), ("10-Q/A", "10-Q"), ("20-F/A", "20-F"), ("40-F/A", "40-F")])
def test_p11c_14_to_17_amended_periodic_form_normalization(raw: str, base: str) -> None:
    form = normalize_sec_form(raw)
    assert form.base_form == base
    assert form.amended is True
    assert form.periodic is True
    assert form.supplemental is False


def test_p11c_18_supplemental_identity_is_accession_bound() -> None:
    for raw, base in (("8-K/A", "8-K"), ("6-K", "6-K")):
        identity = SupplementalFilingIdentity.from_form(
            cik="320193",
            accession_number="0000320193-24-000123",
            form=raw,
            filing_date="2024-10-31",
        )
        assert identity.serialize() == f"US|0000320193|0000320193-24-000123|{base}|2024-10-31"
        assert identity.accession_number_no_dashes == "000032019324000123"
    assert accession_number_without_dashes("0000320193-24-000123") == "000032019324000123"
    with pytest.raises(ValueError, match="invalid SEC accession_number"):
        normalize_accession_number(" 0000320193-24-000123 ")


def test_p11c_19_supplemental_forms_never_build_periodic_slots() -> None:
    company = CompanyRef("US", "320193", None)
    for form in ("8-K", "6-K", "8-K/A", "6-K/A"):
        policy = FilingPolicy((FilingRequirement(form, "FY"),))
        with pytest.raises(ValueError, match="supplemental SEC form"):
            from financial_filing_data_foundation.identity import build_required_slots
            build_required_slots(company, 2025, 2025, policy)
