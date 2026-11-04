from __future__ import annotations

import pytest

from financial_filing_data_foundation.identity import (
    CompanyRef,
    FilingIdentity,
    FilingPolicy,
    FilingRequirement,
    FilingSlotKey,
    SUPPORTED_MARKETS,
    build_required_slots,
)


def test_supported_markets_are_final_cn_hk_scope() -> None:
    assert SUPPORTED_MARKETS == ("CN", "HK")


def test_filing_slot_key_is_stable_and_normalized() -> None:
    slot = FilingSlotKey("cn", "company-1", "annual_report", 2024, "fy")
    assert slot.serialize() == "CN|company-1|ANNUAL_REPORT|2024|FY"


def test_amended_does_not_change_required_slot_key() -> None:
    slot = FilingSlotKey("CN", "c1", "ANNUAL_REPORT", 2024, "FY")
    original = FilingIdentity(slot, amended=False)
    amended = FilingIdentity(slot, amended=True)
    unknown = FilingIdentity(slot, amended=None)

    assert original.slot_key == amended.slot_key == unknown.slot_key


def test_required_slots_preserve_year_then_policy_order() -> None:
    company = CompanyRef("CN", "c1", "600519")
    policy = FilingPolicy(
        (
            FilingRequirement("QUARTERLY_REPORT", "Q1"),
            FilingRequirement("ANNUAL_REPORT", "FY"),
        )
    )

    slots = build_required_slots(company, 2023, 2024, policy)

    assert [s.serialize() for s in slots] == [
        "CN|c1|QUARTERLY_REPORT|2023|Q1",
        "CN|c1|ANNUAL_REPORT|2023|FY",
        "CN|c1|QUARTERLY_REPORT|2024|Q1",
        "CN|c1|ANNUAL_REPORT|2024|FY",
    ]


def test_duplicate_policy_requirement_is_rejected() -> None:
    req = FilingRequirement("ANNUAL_REPORT", "FY")
    with pytest.raises(ValueError, match="duplicate filing requirement"):
        FilingPolicy((req, req))


def test_invalid_year_range_is_rejected() -> None:
    company = CompanyRef("HK", "c1", "00005")
    policy = FilingPolicy((FilingRequirement("ANNUAL_REPORT", "FY"),))
    with pytest.raises(ValueError, match="start_year"):
        build_required_slots(company, 2025, 2024, policy)


def test_p1_market_is_limited_to_cn_hk() -> None:
    with pytest.raises(ValueError, match="unsupported P1 market"):
        CompanyRef("US", "x", "AAPL")
