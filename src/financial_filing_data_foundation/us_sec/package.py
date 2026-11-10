from __future__ import annotations

import hashlib
import json
import os
import shutil
import uuid
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any, Iterable

from .errors import P11Reason, SecError
from .http import validate_sec_url
from .path_policy import normalize_archive_relative_name, validate_archive_member_url


PACKAGE_MANIFEST_SCHEMA = "p11-sec-package-v1"
_PACKAGE_MAX_BYTES = 512 * 1024 * 1024


class SecMemberRole(StrEnum):
    PRIMARY_DOCUMENT = "PRIMARY_DOCUMENT"
    XBRL_INSTANCE = "XBRL_INSTANCE"
    XBRL_SCHEMA = "XBRL_SCHEMA"
    XBRL_PRESENTATION = "XBRL_PRESENTATION"
    XBRL_CALCULATION = "XBRL_CALCULATION"
    XBRL_LABEL = "XBRL_LABEL"
    XBRL_DEFINITION = "XBRL_DEFINITION"
    XBRL_REFERENCE = "XBRL_REFERENCE"
    FILING_SUMMARY = "FILING_SUMMARY"
    COMPLETE_SUBMISSION_TEXT = "COMPLETE_SUBMISSION_TEXT"
    OTHER = "OTHER"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _safe_relative_name(value: str) -> str:
    return normalize_archive_relative_name(value)


@dataclass(frozen=True, slots=True)
class SecPackageMember:
    relative_name: str
    role: SecMemberRole
    content_type: str
    source_url: str
    body: bytes

    def __post_init__(self) -> None:
        object.__setattr__(self, "relative_name", _safe_relative_name(self.relative_name))
        object.__setattr__(self, "content_type", self.content_type.split(";", 1)[0].strip().lower())
        if not self.content_type:
            raise SecError(P11Reason.P11_PACKAGE_INVALID, "package member content_type is required")
        normalized_source_url = self.source_url.strip()
        if not normalized_source_url or normalized_source_url != self.source_url:
            raise SecError(P11Reason.P11_PACKAGE_INVALID, "package member source_url is required")
        try:
            validate_sec_url(normalized_source_url)
            validate_archive_member_url(normalized_source_url)
        except SecError as exc:
            raise SecError(P11Reason.P11_ARCHIVE_HOST_REJECTED, "package member source URL is not allowlisted") from exc
        object.__setattr__(self, "source_url", normalized_source_url)
        if not isinstance(self.body, (bytes, bytearray)):
            raise SecError(P11Reason.P11_PACKAGE_INVALID, "package member body must be bytes")
        object.__setattr__(self, "body", bytes(self.body))

    @property
    def member_sha256(self) -> str:
        return _sha256(self.body)

    def canonical_record(self) -> dict[str, Any]:
        return {
            "role": self.role.value,
            "relative_name": self.relative_name,
            "member_sha256": self.member_sha256,
            "byte_length": len(self.body),
        }

    def manifest_record(self) -> dict[str, Any]:
        return {
            **self.canonical_record(),
            "content_type": self.content_type,
            "source_url": self.source_url,
        }


@dataclass(frozen=True, slots=True)
class SecFilingPackage:
    cik: str
    accession: str
    form: str
    fiscal_year: int
    period: str
    members: tuple[SecPackageMember, ...]
    filing_date: str | None = None
    accepted_at: str | None = None
    report_period: str | None = None
    primary_document: str | None = None
    package_sha256: str = ""

    def __post_init__(self) -> None:
        if not self.members:
            raise SecError(P11Reason.P11_PACKAGE_INVALID, "SEC package must have members")
        names = [member.relative_name for member in self.members]
        if len(names) != len(set(names)):
            raise SecError(P11Reason.P11_PACKAGE_INVALID, "SEC package has duplicate member names")
        if not any(member.role is SecMemberRole.PRIMARY_DOCUMENT for member in self.members):
            raise SecError(P11Reason.P11_PRIMARY_DOCUMENT_MISSING, "SEC package has no primary document")
        if self.package_sha256 and self.package_sha256 != self.compute_package_sha256():
            raise SecError(P11Reason.P11_PACKAGE_INVALID, "SEC package SHA does not match members")

    def canonical_records(self) -> list[dict[str, Any]]:
        return sorted(
            (member.canonical_record() for member in self.members),
            key=lambda row: (str(row["relative_name"]), str(row["role"])),
        )

    def compute_package_sha256(self) -> str:
        encoded = json.dumps(
            self.canonical_records(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return _sha256(encoded)

    @property
    def identity_package_sha256(self) -> str:
        return self.package_sha256 or self.compute_package_sha256()

    def manifest(self) -> dict[str, Any]:
        return {
            "schema_version": PACKAGE_MANIFEST_SCHEMA,
            "package_sha256": self.identity_package_sha256,
            "cik": self.cik,
            "accession": self.accession,
            "form": self.form,
            "fiscal_year": self.fiscal_year,
            "period": self.period,
            "filing_date": self.filing_date,
            "accepted_at": self.accepted_at,
            "report_period": self.report_period,
            "primary_document": self.primary_document,
            "members": [member.manifest_record() for member in self.canonical_members()],
        }

    def canonical_members(self) -> tuple[SecPackageMember, ...]:
        return tuple(sorted(self.members, key=lambda member: (member.relative_name, member.role.value)))


def build_package(
    *,
    cik: str,
    accession: str,
    form: str,
    fiscal_year: int,
    period: str,
    members: Iterable[SecPackageMember],
    filing_date: str | None = None,
    accepted_at: str | None = None,
    report_period: str | None = None,
    primary_document: str | None = None,
) -> SecFilingPackage:
    member_tuple = tuple(members)
    if primary_document is None:
        primary_rows = [member.relative_name for member in member_tuple if member.role is SecMemberRole.PRIMARY_DOCUMENT]
        primary_document = primary_rows[0] if primary_rows else None
    package = SecFilingPackage(
        cik=cik,
        accession=accession,
        form=form.upper(),
        fiscal_year=fiscal_year,
        period=period.upper(),
        members=member_tuple,
        filing_date=filing_date,
        accepted_at=accepted_at,
        report_period=report_period,
        primary_document=primary_document,
    )
    return SecFilingPackage(**{**package.__dict__, "package_sha256": package.compute_package_sha256()}) if hasattr(package, "__dict__") else SecFilingPackage(
        cik=package.cik,
        accession=package.accession,
        form=package.form,
        fiscal_year=package.fiscal_year,
        period=package.period,
        members=package.members,
        filing_date=package.filing_date,
        accepted_at=package.accepted_at,
        report_period=package.report_period,
        primary_document=package.primary_document,
        package_sha256=package.compute_package_sha256(),
    )


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")


class SecPackageStore:
    def __init__(self, raw_store_root: str | Path, *, package_max_bytes: int = _PACKAGE_MAX_BYTES) -> None:
        self.root = Path(raw_store_root).expanduser().resolve()
        self.package_max_bytes = package_max_bytes

    def package_dir(self, package_sha256: str) -> Path:
        normalized = package_sha256.strip().lower()
        if len(normalized) != 64 or any(char not in "0123456789abcdef" for char in normalized):
            raise SecError(P11Reason.P11_PACKAGE_INVALID, "invalid package SHA")
        return self.root / "packages" / "sha256" / normalized[:2] / normalized

    def put(self, package: SecFilingPackage) -> Path:
        package_sha = package.identity_package_sha256
        total = sum(len(member.body) for member in package.members)
        if total > self.package_max_bytes:
            raise SecError(P11Reason.P11_SIZE_LIMIT_EXCEEDED, "SEC package exceeds package size limit")
        existing_accession = self.find_by_accession(package.accession)
        if existing_accession is not None and existing_accession.package_sha256 != package_sha:
            raise SecError(
                P11Reason.P11_SOURCE_DRIFT,
                f"SEC source drift: accession already exists with different package bytes: {package.accession}",
            )
        final_dir = self.package_dir(package_sha)
        if final_dir.exists():
            loaded = self.load(package_sha)
            if loaded.manifest() != package.manifest():
                raise SecError(P11Reason.P11_SOURCE_DRIFT, "existing SEC package differs from requested bytes")
            return final_dir

        # Keep the staging name short: Windows MAX_PATH is still relevant for
        # test workspaces nested below the project root.
        temp_dir = final_dir.parent / f".{uuid.uuid4().hex}.tmp"
        temp_dir.mkdir(parents=True, exist_ok=False)
        try:
            members_dir = temp_dir / "members"
            members_dir.mkdir()
            for member in package.canonical_members():
                target = members_dir / member.relative_name
                try:
                    target.resolve().relative_to(members_dir.resolve())
                except ValueError as exc:
                    raise SecError(P11Reason.P11_PACKAGE_INVALID, "SEC package member escapes package root") from exc
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(member.body)
            _write_json(temp_dir / "manifest.json", package.manifest())
            final_dir.parent.mkdir(parents=True, exist_ok=True)
            try:
                os.replace(temp_dir, final_dir)
            except FileExistsError:
                shutil.rmtree(temp_dir, ignore_errors=True)
                loaded = self.load(package_sha)
                if loaded.manifest() != package.manifest():
                    raise SecError(P11Reason.P11_SOURCE_DRIFT, "SEC package appeared with different bytes")
        except Exception:
            if temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)
            raise
        return final_dir

    def load(self, package_sha256: str) -> SecFilingPackage:
        directory = self.package_dir(package_sha256)
        manifest_path = directory / "manifest.json"
        if not manifest_path.is_file():
            raise SecError(P11Reason.P11_PACKAGE_INVALID, f"SEC package manifest missing: {directory}")
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise SecError(P11Reason.P11_PACKAGE_INVALID, "SEC package manifest is invalid") from exc
        if manifest.get("schema_version") != PACKAGE_MANIFEST_SCHEMA:
            raise SecError(P11Reason.P11_PACKAGE_INVALID, "unsupported SEC package manifest schema")
        members: list[SecPackageMember] = []
        raw_members = manifest.get("members")
        if not isinstance(raw_members, list):
            raise SecError(P11Reason.P11_PACKAGE_INVALID, "SEC package members are missing")
        for raw in raw_members:
            if not isinstance(raw, dict):
                raise SecError(P11Reason.P11_PACKAGE_INVALID, "SEC package member is invalid")
            relative_name = _safe_relative_name(str(raw.get("relative_name", "")))
            path = directory / "members" / relative_name
            try:
                body = path.read_bytes()
            except OSError as exc:
                raise SecError(P11Reason.P11_PACKAGE_INVALID, f"SEC package member missing: {relative_name}") from exc
            expected_sha = str(raw.get("member_sha256", "")).lower()
            if _sha256(body) != expected_sha or len(body) != int(raw.get("byte_length", -1)):
                raise SecError(P11Reason.P11_MEMBER_HASH_MISMATCH, f"SEC package member hash mismatch: {relative_name}")
            try:
                role = SecMemberRole(str(raw["role"]))
            except (KeyError, ValueError) as exc:
                raise SecError(P11Reason.P11_PACKAGE_INVALID, "SEC package member role is invalid") from exc
            members.append(
                SecPackageMember(
                    relative_name=relative_name,
                    role=role,
                    content_type=str(raw.get("content_type", "")),
                    source_url=str(raw.get("source_url", "")),
                    body=body,
                )
            )
        if sum(len(member.body) for member in members) > self.package_max_bytes:
            raise SecError(P11Reason.P11_SIZE_LIMIT_EXCEEDED, "SEC package exceeds package size limit")
        package = SecFilingPackage(
            cik=str(manifest.get("cik", "")),
            accession=str(manifest.get("accession", "")),
            form=str(manifest.get("form", "")),
            fiscal_year=int(manifest.get("fiscal_year")),
            period=str(manifest.get("period", "")),
            members=tuple(members),
            filing_date=manifest.get("filing_date"),
            accepted_at=manifest.get("accepted_at"),
            report_period=manifest.get("report_period"),
            primary_document=manifest.get("primary_document"),
            package_sha256=str(manifest.get("package_sha256", "")),
        )
        if package.identity_package_sha256 != package_sha256.lower():
            raise SecError(P11Reason.P11_PACKAGE_INVALID, "SEC package identity hash mismatch")
        if package.manifest() != manifest:
            raise SecError(P11Reason.P11_PACKAGE_INVALID, "SEC package manifest identity mismatch")
        return package

    def find_by_accession(self, accession: str) -> SecFilingPackage | None:
        manifests_root = self.root / "packages" / "sha256"
        if not manifests_root.is_dir():
            return None
        for manifest_path in sorted(manifests_root.glob("*" + "/*/manifest.json")):
            try:
                raw = json.loads(manifest_path.read_text(encoding="utf-8"))
            except (OSError, UnicodeDecodeError, json.JSONDecodeError):
                continue
            if str(raw.get("accession", "")) != accession:
                continue
            return self.load(str(raw.get("package_sha256", "")))
        return None

    def find_by_slot(self, *, cik: str, fiscal_year: int, period: str) -> SecFilingPackage | None:
        """Return a unique local package for a SEC slot without network access."""

        manifests_root = self.root / "packages" / "sha256"
        if not manifests_root.is_dir():
            return None
        matches: list[SecFilingPackage] = []
        normalized_cik = str(cik).zfill(10)
        normalized_period = str(period).strip().upper()
        for manifest_path in sorted(manifests_root.glob("*" + "/*/manifest.json")):
            try:
                raw = json.loads(manifest_path.read_text(encoding="utf-8"))
                if (
                    str(raw.get("cik", "")) != normalized_cik
                    or int(raw.get("fiscal_year", -1)) != int(fiscal_year)
                    or str(raw.get("period", "")).upper() != normalized_period
                ):
                    continue
                matches.append(self.load(str(raw.get("package_sha256", ""))))
            except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError, SecError):
                continue
        unique = {package.package_sha256: package for package in matches}
        if len(unique) != 1:
            return None
        return next(iter(unique.values()))


__all__ = [
    "PACKAGE_MANIFEST_SCHEMA",
    "SecFilingPackage",
    "SecMemberRole",
    "SecPackageMember",
    "SecPackageStore",
    "build_package",
]
