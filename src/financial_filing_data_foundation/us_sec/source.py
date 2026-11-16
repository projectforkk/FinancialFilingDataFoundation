from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import uuid
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

from .errors import P11Reason, SecError
from .http import PACKAGE_MAX_BYTES, validate_sec_url
from .package import SecFilingPackage
from .path_policy import (
    archive_member_url,
    complete_submission_url,
    complete_submission_url_is_exact,
    normalize_archive_relative_name,
    validate_complete_submission_url,
)


SEC_SOURCE_CONTAINER_SCHEMA = "p11-sec-source-container-v1"
SEC_SOURCE_CONTAINER_KIND = "SEC_COMPLETE_SUBMISSION_TEXT"
SEC_PACKAGE_SOURCE_PROVENANCE_SCHEMA = "p11-sec-package-source-v1"

_ACCESSION_RE = re.compile(r"^\d{10}-\d{2}-\d{6}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_DOCUMENT_OPEN_RE = re.compile(rb"(?im)^<DOCUMENT>[ \t]*(?:\r\n|\n|$)")
_DOCUMENT_CLOSE_RE = re.compile(rb"(?im)^</DOCUMENT>[ \t]*(?:\r\n|\n|$)")
_TEXT_OPEN_RE = re.compile(rb"(?im)^<TEXT>[ \t]*(?:\r\n|\n|$)")
_TEXT_CLOSE_RE = re.compile(rb"(?im)^</TEXT>[ \t]*(?:\r\n|\n|$)")
_FIELD_NAMES = (b"TYPE", b"SEQUENCE", b"FILENAME")
_ACTIVE_CONTENT_RE = re.compile(rb"<\s*(?:script|applet|object|iframe|embed)\b", re.IGNORECASE)
_HTML_NAME_SUFFIXES = (".htm", ".html", ".xhtml")
_XML_NAME_SUFFIXES = (".xml", ".xsd", ".xbrl")


def _sha256(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def _canonical_json(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _require_sha(value: str, label: str) -> str:
    normalized = str(value).strip().lower()
    if not _SHA256_RE.fullmatch(normalized):
        raise SecError(P11Reason.P11_PACKAGE_INVALID, f"{label} is invalid")
    return normalized


def _extended_path(path: Path) -> Path:
    """Use the Windows long-path namespace for deep identity paths."""

    raw = str(path)
    if os.name == "nt" and len(raw) >= 240 and not raw.startswith("\\\\?\\"):
        return Path("\\\\?\\" + os.path.abspath(raw))
    return path


def _require_cik(value: str) -> str:
    normalized = str(value).strip()
    if not normalized.isdigit() or len(normalized) != 10:
        raise SecError(P11Reason.P11_INVALID_US_IDENTITY, "SEC CIK is not normalized")
    return normalized


def _require_accession(value: str) -> str:
    normalized = str(value).strip()
    if not _ACCESSION_RE.fullmatch(normalized):
        raise SecError(P11Reason.P11_PACKAGE_INVALID, "SEC accession is invalid")
    return normalized


@dataclass(frozen=True, slots=True)
class SecSourceContainer:
    schema_version: str
    kind: str
    source_url: str
    source_container_sha256: str
    byte_length: int
    cik: str
    accession: str
    body: bytes

    def __post_init__(self) -> None:
        if self.schema_version != SEC_SOURCE_CONTAINER_SCHEMA:
            raise SecError(P11Reason.P11_PACKAGE_INVALID, "unsupported SEC source-container schema")
        if self.kind != SEC_SOURCE_CONTAINER_KIND:
            raise SecError(P11Reason.P11_PACKAGE_INVALID, "unsupported SEC source-container kind")
        cik = _require_cik(self.cik)
        accession = _require_accession(self.accession)
        source_url = validate_sec_url(self.source_url)
        source_url = validate_complete_submission_url(source_url)
        if not complete_submission_url_is_exact(source_url, cik=cik, accession=accession):
            raise SecError(P11Reason.P11_PROVENANCE_MISMATCH, "SEC source-container URL is not bound to its identity")
        if not isinstance(self.body, (bytes, bytearray)) or not self.body:
            raise SecError(P11Reason.P11_PACKAGE_INVALID, "SEC source-container body is empty")
        body = bytes(self.body)
        source_sha = _require_sha(self.source_container_sha256, "SEC source-container SHA")
        if source_sha != _sha256(body) or int(self.byte_length) != len(body):
            raise SecError(P11Reason.P11_SOURCE_DRIFT, "SEC source-container hash or length mismatch")
        if len(body) > PACKAGE_MAX_BYTES:
            raise SecError(P11Reason.P11_SIZE_LIMIT_EXCEEDED, "SEC source-container exceeds package size limit")
        object.__setattr__(self, "cik", cik)
        object.__setattr__(self, "accession", accession)
        object.__setattr__(self, "source_url", source_url)
        object.__setattr__(self, "source_container_sha256", source_sha)
        object.__setattr__(self, "byte_length", len(body))
        object.__setattr__(self, "body", body)

    @classmethod
    def from_bytes(cls, body: bytes, *, cik: str, accession: str, source_url: str | None = None) -> "SecSourceContainer":
        normalized_cik = _require_cik(cik)
        normalized_accession = _require_accession(accession)
        return cls(
            schema_version=SEC_SOURCE_CONTAINER_SCHEMA,
            kind=SEC_SOURCE_CONTAINER_KIND,
            source_url=source_url or complete_submission_url(normalized_cik, normalized_accession),
            source_container_sha256=_sha256(bytes(body)),
            byte_length=len(body),
            cik=normalized_cik,
            accession=normalized_accession,
            body=bytes(body),
        )

    def metadata(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "kind": self.kind,
            "source_url": self.source_url,
            "source_container_sha256": self.source_container_sha256,
            "byte_length": self.byte_length,
            "cik": self.cik,
            "accession": self.accession,
        }


class SecSourceContainerStore:
    def __init__(self, raw_store_root: str | Path, *, max_bytes: int = PACKAGE_MAX_BYTES) -> None:
        self.root = Path(raw_store_root).expanduser().resolve()
        self.max_bytes = int(max_bytes)

    def container_dir(self, source_container_sha256: str) -> Path:
        sha = _require_sha(source_container_sha256, "SEC source-container SHA")
        return self.root / "sec-containers" / "sha256" / sha[:2] / sha

    def put(self, container: SecSourceContainer) -> Path:
        if len(container.body) > self.max_bytes:
            raise SecError(P11Reason.P11_SIZE_LIMIT_EXCEEDED, "SEC source-container exceeds configured size limit")
        final_dir = self.container_dir(container.source_container_sha256)
        if final_dir.exists():
            loaded = self.load(container.source_container_sha256)
            if loaded.metadata() != container.metadata() or loaded.body != container.body:
                raise SecError(P11Reason.P11_SOURCE_DRIFT, "existing SEC source-container differs from requested bytes")
            return final_dir
        final_dir.parent.mkdir(parents=True, exist_ok=True)
        # Keep the staging path short for Windows worktrees nested below the
        # project root; the final identity path remains the frozen contract.
        self.root.mkdir(parents=True, exist_ok=True)
        temp_dir = self.root / f".sp-{uuid.uuid4().hex}.tmp"
        temp_dir.mkdir(parents=False, exist_ok=False)
        try:
            (temp_dir / "source.txt").write_bytes(container.body)
            (temp_dir / "metadata.json").write_text(
                json.dumps(container.metadata(), ensure_ascii=False, sort_keys=True, indent=2) + "\n",
                encoding="utf-8",
            )
            if _sha256((temp_dir / "source.txt").read_bytes()) != container.source_container_sha256:
                raise SecError(P11Reason.P11_SOURCE_DRIFT, "SEC source-container staging hash mismatch")
            try:
                os.replace(temp_dir, final_dir)
            except FileExistsError:
                shutil.rmtree(temp_dir, ignore_errors=True)
                loaded = self.load(container.source_container_sha256)
                if loaded.metadata() != container.metadata() or loaded.body != container.body:
                    raise SecError(P11Reason.P11_SOURCE_DRIFT, "SEC source-container appeared with different bytes")
        except Exception:
            if temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)
            raise
        return final_dir

    def load(self, source_container_sha256: str) -> SecSourceContainer:
        directory = self.container_dir(source_container_sha256)
        metadata_path = directory / "metadata.json"
        source_path = directory / "source.txt"
        try:
            payload = json.loads(metadata_path.read_text(encoding="utf-8"))
            body = source_path.read_bytes()
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise SecError(P11Reason.P11_PACKAGE_INVALID, "SEC source-container files are invalid") from exc
        if not isinstance(payload, dict):
            raise SecError(P11Reason.P11_PACKAGE_INVALID, "SEC source-container metadata is invalid")
        if payload.get("schema_version") != SEC_SOURCE_CONTAINER_SCHEMA:
            raise SecError(P11Reason.P11_PACKAGE_INVALID, "unsupported SEC source-container schema")
        try:
            container = SecSourceContainer(
                schema_version=str(payload["schema_version"]),
                kind=str(payload["kind"]),
                source_url=str(payload["source_url"]),
                source_container_sha256=str(payload["source_container_sha256"]),
                byte_length=int(payload["byte_length"]),
                cik=str(payload["cik"]),
                accession=str(payload["accession"]),
                body=body,
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise SecError(P11Reason.P11_PACKAGE_INVALID, "SEC source-container metadata is incomplete") from exc
        if container.source_container_sha256 != str(source_container_sha256).lower() or container.metadata() != payload:
            raise SecError(P11Reason.P11_SOURCE_DRIFT, "SEC source-container path or metadata identity mismatch")
        return container

    def find_by_accession(self, *, cik: str, accession: str) -> tuple[SecSourceContainer, ...]:
        root = self.root / "sec-containers" / "sha256"
        if not root.is_dir():
            return ()
        rows: list[SecSourceContainer] = []
        for metadata_path in sorted(root.glob("*/*/metadata.json")):
            try:
                payload = json.loads(metadata_path.read_text(encoding="utf-8"))
                if str(payload.get("cik")) != str(cik).zfill(10) or str(payload.get("accession")) != accession:
                    continue
                rows.append(self.load(str(payload.get("source_container_sha256", ""))))
            except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError, SecError):
                continue
        return tuple(sorted(rows, key=lambda row: row.source_container_sha256))


@dataclass(frozen=True, slots=True)
class SecSgmlDocument:
    document_index: int
    document_type: str
    document_sequence: str
    filename: str
    text_start: int
    text_end: int
    payload_start: int
    payload_end: int
    payload_envelope: str

    def payload(self, body: bytes) -> bytes:
        if not (0 <= self.payload_start <= self.payload_end <= len(body)):
            raise SecError(P11Reason.P11_PACKAGE_INVALID, "SEC SGML payload locator is out of bounds")
        return body[self.payload_start : self.payload_end]

    def validate_payload(self, body: bytes, *, primary: bool = False) -> None:
        payload = self.payload(body)
        lower = self.filename.casefold()
        if not payload:
            raise SecError(P11Reason.P11_CONTENT_TYPE_INVALID, f"SEC member is empty: {self.filename}")
        if primary or lower.endswith(_HTML_NAME_SUFFIXES):
            try:
                text = payload.decode("utf-8-sig")
                parser = HTMLParser(convert_charrefs=True)
                parser.feed(text)
                parser.close()
            except (UnicodeDecodeError, AssertionError, ValueError) as exc:
                raise SecError(P11Reason.P11_CONTENT_TYPE_INVALID, f"SEC primary HTML bytes are invalid: {self.filename}") from exc
            if "<html" not in text.casefold():
                raise SecError(P11Reason.P11_CONTENT_TYPE_INVALID, f"SEC primary member is not HTML: {self.filename}")
            if primary and _ACTIVE_CONTENT_RE.search(payload):
                raise SecError(P11Reason.P11_CONTENT_TYPE_INVALID, f"SEC canonical primary contains active content: {self.filename}")
        elif lower.endswith(_XML_NAME_SUFFIXES):
            try:
                ET.fromstring(payload)
            except ET.ParseError as exc:
                raise SecError(P11Reason.P11_CONTENT_TYPE_INVALID, f"SEC XML member bytes are invalid: {self.filename}") from exc

    def locator(self, *, role: str, public_source_url: str, body: bytes) -> dict[str, Any]:
        return {
            "relative_name": self.filename,
            "role": role,
            "public_source_url": public_source_url,
            "member_sha256": _sha256(self.payload(body)),
            "byte_length": self.payload_end - self.payload_start,
            "document_index": self.document_index,
            "document_type": self.document_type,
            "document_sequence": self.document_sequence,
            "filename": self.filename,
            "payload_start": self.payload_start,
            "payload_end": self.payload_end,
            "payload_envelope": self.payload_envelope,
        }


@dataclass(frozen=True, slots=True)
class SecSgmlInventory:
    cik: str
    accession: str
    documents: tuple[SecSgmlDocument, ...]
    source_sha256: str | None = None

    def by_filename(self, filename: str) -> SecSgmlDocument:
        normalized = normalize_archive_relative_name(filename)
        matches = [row for row in self.documents if row.filename == normalized]
        if len(matches) != 1:
            raise SecError(P11Reason.P11_PRIMARY_DOCUMENT_MISSING, f"SEC SGML filename is not unique: {normalized}")
        return matches[0]


def _field_value(segment: bytes, field: bytes) -> str:
    pattern = re.compile(rb"(?im)^<" + re.escape(field) + rb">[ \t]*([^\r\n]*)")
    matches = list(pattern.finditer(segment))
    if len(matches) != 1:
        raise SecError(P11Reason.P11_PACKAGE_INVALID, f"SEC SGML document field is missing or duplicated: {field.decode()}")
    try:
        value = matches[0].group(1).decode("ascii").strip()
    except UnicodeDecodeError as exc:
        raise SecError(P11Reason.P11_PACKAGE_INVALID, "SEC SGML structural field is not ASCII") from exc
    if not value:
        raise SecError(P11Reason.P11_PACKAGE_INVALID, "SEC SGML structural field is empty")
    return value


def parse_sec_submission(body: bytes, *, cik: str, accession: str) -> SecSgmlInventory:
    """Parse SEC DOCUMENT envelopes while retaining byte offsets only."""

    if not isinstance(body, (bytes, bytearray)) or not body:
        raise SecError(P11Reason.P11_PACKAGE_INVALID, "SEC complete submission is empty")
    normalized_cik = _require_cik(cik)
    normalized_accession = _require_accession(accession)
    raw = bytes(body)
    identity = re.search(rb"(?im)^<SEC-DOCUMENT>[ \t]*([^\r\n]+)", raw)
    if identity is None:
        raise SecError(P11Reason.P11_PACKAGE_INVALID, "SEC complete submission identity is missing")
    try:
        identity_value = identity.group(1).decode("ascii").strip().split()[0]
    except (UnicodeDecodeError, IndexError) as exc:
        raise SecError(P11Reason.P11_PACKAGE_INVALID, "SEC complete submission identity is invalid") from exc
    if identity_value.casefold().removesuffix(".txt") != normalized_accession.casefold():
        raise SecError(P11Reason.P11_PROVENANCE_MISMATCH, "SEC complete submission accession differs from selected accession")
    document_opens = list(_DOCUMENT_OPEN_RE.finditer(raw))
    document_closes = list(_DOCUMENT_CLOSE_RE.finditer(raw))
    if not document_opens or len(document_opens) != len(document_closes):
        raise SecError(P11Reason.P11_PACKAGE_INVALID, "SEC complete submission DOCUMENT nesting is malformed")
    documents: list[SecSgmlDocument] = []
    last_end = -1
    seen_names: set[str] = set()
    for index, opening in enumerate(document_opens, start=1):
        if opening.start() < last_end:
            raise SecError(P11Reason.P11_PACKAGE_INVALID, "SEC complete submission DOCUMENT nesting overlaps")
        closing = next((row for row in document_closes if row.start() > opening.end()), None)
        if closing is None or (index < len(document_opens) and closing.start() > document_opens[index].start()):
            raise SecError(P11Reason.P11_PACKAGE_INVALID, "SEC complete submission DOCUMENT closing tag is malformed")
        segment = raw[opening.end() : closing.start()]
        text_match = _TEXT_OPEN_RE.search(segment)
        text_closes = list(_TEXT_CLOSE_RE.finditer(segment))
        if text_match is None or len(text_closes) != 1 or text_closes[0].start() < text_match.end():
            raise SecError(P11Reason.P11_PACKAGE_INVALID, "SEC SGML TEXT envelope is malformed")
        text_close = text_closes[0]
        document_type = _field_value(segment[: text_match.start()], b"TYPE")
        document_sequence = _field_value(segment[: text_match.start()], b"SEQUENCE")
        if not document_sequence.isdigit():
            raise SecError(P11Reason.P11_PACKAGE_INVALID, "SEC SGML document sequence is invalid")
        filename = normalize_archive_relative_name(_field_value(segment[: text_match.start()], b"FILENAME"))
        if filename in seen_names:
            raise SecError(P11Reason.P11_PACKAGE_INVALID, f"SEC SGML filename is duplicated: {filename}")
        seen_names.add(filename)
        text_start = opening.end() + text_match.end()
        text_end = opening.end() + text_close.start()
        payload_start = text_start
        payload_end = text_end
        envelope = "TEXT"
        text_body = raw[text_start:text_end]
        inner_open = re.search(rb"(?im)^[ \t]*<(XML|XBRL)>[ \t]*(?:\r\n|\n|$)", text_body)
        inner_close = list(re.finditer(rb"(?im)^</(XML|XBRL)>[ \t]*(?:\r\n|\n|$)", text_body))
        if inner_open is not None:
            inner_name = inner_open.group(1).decode("ascii").upper()
            matching = [row for row in inner_close if row.group(1).decode("ascii").upper() == inner_name and row.start() >= inner_open.end()]
            if len(matching) != 1 or text_body[: inner_open.start()].strip() or text_body[matching[0].end() :].strip():
                raise SecError(P11Reason.P11_PACKAGE_INVALID, "SEC XML/XBRL envelope is malformed")
            envelope = inner_name
            payload_start = text_start + inner_open.end()
            payload_end = text_start + matching[0].start()
        documents.append(
            SecSgmlDocument(
                document_index=index,
                document_type=document_type,
                document_sequence=document_sequence,
                filename=filename,
                text_start=text_start,
                text_end=text_end,
                payload_start=payload_start,
                payload_end=payload_end,
                payload_envelope=envelope,
            )
        )
        last_end = closing.end()
    return SecSgmlInventory(normalized_cik, normalized_accession, tuple(documents), _sha256(raw))


@dataclass(frozen=True, slots=True)
class SecPackageSourceProvenance:
    payload: dict[str, Any]

    def __post_init__(self) -> None:
        if not isinstance(self.payload, dict) or self.payload.get("schema_version") != SEC_PACKAGE_SOURCE_PROVENANCE_SCHEMA:
            raise SecError(P11Reason.P11_PACKAGE_INVALID, "unsupported SEC package-source provenance schema")
        required = {
            "schema_version",
            "provenance_sha256",
            "package_sha256",
            "cik",
            "accession",
            "source_container",
            "members",
        }
        if set(self.payload) != required:
            raise SecError(P11Reason.P11_PACKAGE_INVALID, "SEC package-source provenance fields are invalid")
        if not isinstance(self.payload.get("source_container"), dict):
            raise SecError(P11Reason.P11_PACKAGE_INVALID, "SEC provenance source-container metadata is invalid")
        if not isinstance(self.payload.get("members"), list):
            raise SecError(P11Reason.P11_PACKAGE_INVALID, "SEC provenance members are invalid")
        _require_cik(str(self.payload.get("cik", "")))
        _require_accession(str(self.payload.get("accession", "")))
        _require_sha(str(self.payload.get("package_sha256", "")), "SEC package SHA")
        supplied = _require_sha(str(self.payload.get("provenance_sha256", "")), "SEC provenance SHA")
        unsigned = dict(self.payload)
        unsigned.pop("provenance_sha256", None)
        if supplied != _sha256(_canonical_json(unsigned)):
            raise SecError(P11Reason.P11_PROVENANCE_MISMATCH, "SEC package-source provenance hash mismatch")
        object.__setattr__(self, "payload", json.loads(json.dumps(self.payload, ensure_ascii=False, sort_keys=True)))

    @property
    def provenance_sha256(self) -> str:
        return str(self.payload["provenance_sha256"])

    @property
    def package_sha256(self) -> str:
        return str(self.payload["package_sha256"])

    @property
    def source_container_sha256(self) -> str:
        return str(self.payload["source_container"]["source_container_sha256"])

    @property
    def accession(self) -> str:
        return str(self.payload["accession"])

    @property
    def cik(self) -> str:
        return str(self.payload["cik"])

    def to_dict(self) -> dict[str, Any]:
        return json.loads(json.dumps(self.payload, ensure_ascii=False, sort_keys=True))


def build_package_source_provenance(
    package: SecFilingPackage,
    container: SecSourceContainer,
    inventory: SecSgmlInventory,
) -> SecPackageSourceProvenance:
    if package.cik != container.cik or package.accession != container.accession or inventory.cik != container.cik or inventory.accession != container.accession:
        raise SecError(P11Reason.P11_PROVENANCE_MISMATCH, "SEC package/source-container identity differs")
    members: list[dict[str, Any]] = []
    for member in package.canonical_members():
        document = inventory.by_filename(member.relative_name)
        payload = document.payload(container.body)
        if payload != member.body:
            raise SecError(P11Reason.P11_PROVENANCE_MISMATCH, f"SEC package member is not a source-container slice: {member.relative_name}")
        members.append(document.locator(role=member.role.value, public_source_url=member.source_url, body=container.body))
    unsigned: dict[str, Any] = {
        "schema_version": SEC_PACKAGE_SOURCE_PROVENANCE_SCHEMA,
        "package_sha256": package.package_sha256,
        "cik": package.cik,
        "accession": package.accession,
        "source_container": container.metadata(),
        "members": sorted(members, key=lambda row: str(row["relative_name"])),
    }
    unsigned["provenance_sha256"] = _sha256(_canonical_json(unsigned))
    return SecPackageSourceProvenance(unsigned)


class SecPackageSourceProvenanceStore:
    def __init__(self, raw_store_root: str | Path) -> None:
        self.root = Path(raw_store_root).expanduser().resolve()

    def provenance_dir(self, package_sha256: str, provenance_sha256: str) -> Path:
        return _extended_path(
            self.root
            / "sec-package-provenance"
            / "packages"
            / _require_sha(package_sha256, "package SHA")
            / _require_sha(provenance_sha256, "provenance SHA")
        )

    def put(self, provenance: SecPackageSourceProvenance) -> Path:
        final_dir = self.provenance_dir(provenance.package_sha256, provenance.provenance_sha256)
        if final_dir.exists():
            loaded = self.load(provenance.package_sha256, provenance.provenance_sha256)
            if loaded.to_dict() != provenance.to_dict():
                raise SecError(P11Reason.P11_PROVENANCE_MISMATCH, "existing SEC provenance differs from requested identity")
            return final_dir
        final_dir.parent.mkdir(parents=True, exist_ok=True)
        # Keep staging short on Windows; the final path is the identity path.
        self.root.mkdir(parents=True, exist_ok=True)
        temp_dir = self.root / f".sp-{uuid.uuid4().hex}.tmp"
        temp_dir.mkdir(parents=False, exist_ok=False)
        try:
            (temp_dir / "provenance.json").write_text(
                json.dumps(provenance.to_dict(), ensure_ascii=False, sort_keys=True, indent=2) + "\n",
                encoding="utf-8",
            )
            try:
                os.replace(temp_dir, final_dir)
            except FileExistsError:
                shutil.rmtree(temp_dir, ignore_errors=True)
                loaded = self.load(provenance.package_sha256, provenance.provenance_sha256)
                if loaded.to_dict() != provenance.to_dict():
                    raise SecError(P11Reason.P11_PROVENANCE_MISMATCH, "SEC provenance appeared with different identity")
        except Exception:
            if temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)
            raise
        return final_dir

    def load(self, package_sha256: str, provenance_sha256: str) -> SecPackageSourceProvenance:
        path = self.provenance_dir(package_sha256, provenance_sha256) / "provenance.json"
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise SecError(P11Reason.P11_PACKAGE_INVALID, "SEC package-source provenance is invalid") from exc
        if not isinstance(payload, dict) or payload.get("schema_version") != SEC_PACKAGE_SOURCE_PROVENANCE_SCHEMA:
            raise SecError(P11Reason.P11_PACKAGE_INVALID, "unsupported SEC package-source provenance schema")
        try:
            provenance = SecPackageSourceProvenance(payload)
        except (KeyError, TypeError, ValueError) as exc:
            raise SecError(P11Reason.P11_PACKAGE_INVALID, "SEC package-source provenance is incomplete") from exc
        if provenance.package_sha256 != str(package_sha256).lower() or provenance.provenance_sha256 != str(provenance_sha256).lower():
            raise SecError(P11Reason.P11_PROVENANCE_MISMATCH, "SEC package-source provenance path identity mismatch")
        return provenance

    def list_for_package(self, package_sha256: str) -> tuple[SecPackageSourceProvenance, ...]:
        root = _extended_path(self.root / "sec-package-provenance" / "packages" / _require_sha(package_sha256, "package SHA"))
        if not root.is_dir():
            return ()
        rows: list[SecPackageSourceProvenance] = []
        try:
            entries = sorted((Path(entry.path) for entry in os.scandir(root) if entry.is_dir()), key=lambda path: path.name)
        except OSError:
            return ()
        for directory in entries:
            path = directory / "provenance.json"
            try:
                rows.append(self.load(package_sha256, directory.name))
            except SecError:
                continue
        return tuple(rows)


def replay_package_source_provenance(
    package: SecFilingPackage,
    source_store: SecSourceContainerStore,
    provenance_store: SecPackageSourceProvenanceStore,
    provenance_sha256: str | None = None,
) -> SecPackageSourceProvenance:
    if provenance_sha256:
        provenance = provenance_store.load(package.package_sha256, provenance_sha256)
    else:
        candidates = provenance_store.list_for_package(package.package_sha256)
        if not candidates:
            raise SecError(P11Reason.P11_PROVENANCE_MISMATCH, "SEC package has no current source provenance")
        provenance = candidates[0]
    if provenance is None:
        raise SecError(P11Reason.P11_PROVENANCE_MISMATCH, "SEC package has no current source provenance")
    if provenance.package_sha256 != package.package_sha256 or provenance.cik != package.cik or provenance.accession != package.accession:
        raise SecError(P11Reason.P11_PROVENANCE_MISMATCH, "SEC provenance package identity mismatch")
    container = source_store.load(provenance.source_container_sha256)
    source_meta = provenance.payload.get("source_container")
    if source_meta != container.metadata():
        raise SecError(P11Reason.P11_PROVENANCE_MISMATCH, "SEC provenance source-container metadata mismatch")
    inventory = parse_sec_submission(container.body, cik=container.cik, accession=container.accession)
    raw_members = provenance.payload.get("members")
    if not isinstance(raw_members, list):
        raise SecError(P11Reason.P11_PACKAGE_INVALID, "SEC provenance members are invalid")
    package_members = {member.relative_name: member for member in package.members}
    if {str(row.get("relative_name")) for row in raw_members if isinstance(row, dict)} != set(package_members):
        raise SecError(P11Reason.P11_PROVENANCE_MISMATCH, "SEC provenance member set differs from package")
    for row in raw_members:
        if not isinstance(row, dict):
            raise SecError(P11Reason.P11_PACKAGE_INVALID, "SEC provenance member row is invalid")
        name = normalize_archive_relative_name(str(row.get("relative_name", "")))
        member = package_members.get(name)
        if member is None:
            raise SecError(P11Reason.P11_PROVENANCE_MISMATCH, f"SEC provenance member is not in package: {name}")
        document = inventory.by_filename(name)
        expected = document.locator(role=member.role.value, public_source_url=member.source_url, body=container.body)
        for field in expected:
            if row.get(field) != expected[field]:
                raise SecError(P11Reason.P11_PROVENANCE_MISMATCH, f"SEC provenance locator differs for {name}: {field}")
        if document.payload(container.body) != member.body:
            raise SecError(P11Reason.P11_PROVENANCE_MISMATCH, f"SEC provenance replay differs for {name}")
    return provenance


__all__ = [
    "SEC_PACKAGE_SOURCE_PROVENANCE_SCHEMA",
    "SEC_SOURCE_CONTAINER_KIND",
    "SEC_SOURCE_CONTAINER_SCHEMA",
    "SecPackageSourceProvenance",
    "SecPackageSourceProvenanceStore",
    "SecSgmlDocument",
    "SecSgmlInventory",
    "SecSourceContainer",
    "SecSourceContainerStore",
    "build_package_source_provenance",
    "parse_sec_submission",
    "replay_package_source_provenance",
]
