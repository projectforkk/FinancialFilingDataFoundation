from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class SecContentClass(StrEnum):
    TICKER_MAPPING_JSON = "TICKER_MAPPING_JSON"
    SUBMISSIONS_CURRENT_JSON = "SUBMISSIONS_CURRENT_JSON"
    SUBMISSIONS_HISTORY_JSON = "SUBMISSIONS_HISTORY_JSON"


@dataclass(frozen=True, slots=True)
class SecHttpResponse:
    requested_url: str
    final_url: str
    status: int
    content_type: str
    body: bytes
    outbound_start_count: int
    redirect_count: int


@dataclass(frozen=True, slots=True)
class SecDiscoveryCandidate:
    cik: str
    accession_number: str
    form: str
    base_form: str
    amended: bool
    filing_date: str
    report_date: str | None
    primary_document: str
    primary_doc_description: str | None
    is_xbrl: bool
    is_inline_xbrl: bool
    submission_source_urls: tuple[str, ...] = field(compare=False)