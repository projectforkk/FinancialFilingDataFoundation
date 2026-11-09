from __future__ import annotations

import json
from dataclasses import dataclass
from urllib.parse import urljoin

from .discovery import discover_filings, parse_submissions, select_filing
from .http import SecHttpClient
from .models import SecCompanyRef, SecFilingCandidate
from .package import SecFilingPackage, SecMemberRole, SecPackageMember, SecPackageStore, build_package


@dataclass(frozen=True, slots=True)
class SecAcquisitionResult:
    package: SecFilingPackage
    candidate: SecFilingCandidate
    reused: bool


def _content_types(relative_name: str) -> tuple[str, ...]:
    lower = relative_name.casefold()
    if lower.endswith((".htm", ".html")):
        return ("text/html", "application/xhtml+xml")
    if lower.endswith(".json"):
        return ("application/json", "text/json")
    if lower.endswith((".xml", ".xsd")):
        return ("application/xml", "text/xml", "application/xhtml+xml")
    return ("application/octet-stream", "application/pdf", "text/plain")


def _member_role(name: str, primary: str) -> SecMemberRole:
    lower = name.casefold()
    if name == primary:
        return SecMemberRole.PRIMARY_DOCUMENT
    if lower == "filingsummary.xml":
        return SecMemberRole.FILING_SUMMARY
    if lower.endswith(".xsd"):
        return SecMemberRole.XBRL_SCHEMA
    if lower.endswith("_pre.xml"):
        return SecMemberRole.XBRL_PRESENTATION
    if lower.endswith("_cal.xml"):
        return SecMemberRole.XBRL_CALCULATION
    if lower.endswith("_lab.xml"):
        return SecMemberRole.XBRL_LABEL
    if lower.endswith(".xml"):
        return SecMemberRole.XBRL_INSTANCE
    return SecMemberRole.OTHER


class SecAcquirer:
    def __init__(self, client: SecHttpClient, package_store: SecPackageStore) -> None:
        self.client = client
        self.package_store = package_store

    def acquire(
        self,
        company: SecCompanyRef,
        *,
        fiscal_year: int,
        period: str,
    ) -> SecAcquisitionResult:
        submissions_url = f"https://data.sec.gov/submissions/CIK{company.cik}.json"
        response = self.client.fetch(
            submissions_url,
            expected_content_types=("application/json",),
            max_bytes=self.client.config.submissions_max_bytes,
        )
        try:
            payload = json.loads(response.body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            from .errors import P11Reason, SecError

            raise SecError(P11Reason.P11_SEC_DISCOVERY_FAILED, "SEC submissions response is invalid JSON") from exc
        submissions = parse_submissions(payload, company=company, source_url=submissions_url)
        candidates = discover_filings(submissions, fiscal_year=fiscal_year, period=period)
        candidate = select_filing(candidates)
        existing = self.package_store.find_by_accession(candidate.accession)
        if existing is not None:
            return SecAcquisitionResult(package=existing, candidate=candidate, reused=True)
        base_url = candidate.source_url.rsplit("/", 1)[0] + "/"
        index_url = urljoin(base_url, "index.json")
        index_response = self.client.fetch(index_url, expected_content_types=("application/json",), max_bytes=self.client.config.submissions_max_bytes)
        try:
            index_payload = json.loads(index_response.body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            from .errors import P11Reason, SecError

            raise SecError(P11Reason.P11_SEC_DISCOVERY_FAILED, "SEC archive index is invalid JSON") from exc
        raw_items = index_payload.get("directory", {}).get("item") if isinstance(index_payload, dict) else None
        names = [str(item.get("name", "")) for item in raw_items if isinstance(item, dict) and item.get("name")]
        selected = [candidate.primary_document]
        for name in sorted(set(names), key=str.casefold):
            lower = name.casefold()
            if name == candidate.primary_document:
                continue
            if lower.endswith((".xsd", ".xml")):
                selected.append(name)
        members: list[SecPackageMember] = []
        for name in selected:
            member_url = urljoin(base_url, name)
            member_response = self.client.fetch(
                member_url,
                expected_content_types=_content_types(name),
                max_bytes=self.client.config.member_max_bytes,
            )
            members.append(
                SecPackageMember(
                    relative_name=name,
                    role=_member_role(name, candidate.primary_document),
                    content_type=(next((str(key).split(";", 1)[0].strip().lower() for key, value in member_response.headers.items() if str(key).casefold() == "content-type"), _content_types(name)[0])),
                    source_url=member_url,
                    body=member_response.body,
                )
            )
        package = build_package(
            cik=company.cik,
            accession=candidate.accession,
            form=candidate.form,
            fiscal_year=fiscal_year,
            period=period,
            members=members,
            filing_date=candidate.filing_date,
            report_period=candidate.report_period,
            primary_document=candidate.primary_document,
        )
        existed = self.package_store.package_dir(package.package_sha256).exists()
        self.package_store.put(package)
        return SecAcquisitionResult(package=package, candidate=candidate, reused=existed)


__all__ = ["SecAcquirer", "SecAcquisitionResult"]
