from __future__ import annotations

import re
from pathlib import PurePosixPath
from urllib.parse import unquote, urlsplit

from .errors import P11Reason, SecError


_ACCESSION_RE = re.compile(r"^\d{10}-\d{2}-\d{6}$")
_NORMALIZED_ACCESSION_RE = re.compile(r"^\d{18}$")
_DRIVE_RE = re.compile(r"^[A-Za-z]:")
_CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")
_WINDOWS_FORBIDDEN_RE = re.compile(r'[<>:"|?*]')
_WINDOWS_RESERVED_NAMES = {"CON", "PRN", "AUX", "NUL", *(f"COM{index}" for index in range(1, 10)), *(f"LPT{index}" for index in range(1, 10))}


def normalize_archive_relative_name(value: str) -> str:
    """Return one canonical SEC archive-relative path or fail closed.

    SEC archive names may contain nested POSIX directories.  Backslashes,
    encoded traversal, URL syntax, drive-qualified paths and non-canonical
    dot segments are never accepted because the same value is used for both
    URL construction and Windows filesystem storage.
    """

    if not isinstance(value, str) or not value or value != value.strip():
        raise SecError(P11Reason.P11_PACKAGE_INVALID, "SEC archive member path is not canonical")
    if "\\" in value or _CONTROL_RE.search(value):
        raise SecError(P11Reason.P11_PACKAGE_INVALID, "SEC archive member path contains unsafe characters")
    if _DRIVE_RE.match(value) or value.startswith(("/", "//")):
        raise SecError(P11Reason.P11_PACKAGE_INVALID, "SEC archive member path is absolute")
    parsed = urlsplit(value)
    if parsed.scheme or parsed.netloc or parsed.query or parsed.fragment:
        raise SecError(P11Reason.P11_PACKAGE_INVALID, "SEC archive member path contains URL syntax")
    decoded = unquote(value)
    if decoded != value:
        raise SecError(P11Reason.P11_PACKAGE_INVALID, "SEC archive member path contains encoded bytes")
    path = PurePosixPath(value)
    if not path.parts or any(part in {"", ".", ".."} for part in path.parts):
        raise SecError(P11Reason.P11_PACKAGE_INVALID, "SEC archive member path contains traversal")
    if path.as_posix() != value:
        raise SecError(P11Reason.P11_PACKAGE_INVALID, "SEC archive member path is not canonical")
    for part in path.parts:
        if _WINDOWS_FORBIDDEN_RE.search(part) or part.endswith((".", " ")):
            raise SecError(P11Reason.P11_PACKAGE_INVALID, "SEC archive member path is not Windows-safe")
        if part.split(".", 1)[0].upper() in _WINDOWS_RESERVED_NAMES:
            raise SecError(P11Reason.P11_PACKAGE_INVALID, "SEC archive member path uses a reserved Windows name")
    return value


def archive_root_url(cik: str, accession: str) -> str:
    normalized_cik = str(cik).strip()
    if not normalized_cik.isdigit() or len(normalized_cik) != 10:
        raise SecError(P11Reason.P11_INVALID_US_IDENTITY, "SEC archive CIK is not normalized")
    if not _ACCESSION_RE.fullmatch(str(accession)):
        raise SecError(P11Reason.P11_SEC_DISCOVERY_FAILED, "SEC archive accession is invalid")
    return f"https://www.sec.gov/Archives/edgar/data/{int(normalized_cik)}/{str(accession).replace('-', '')}/"


def archive_member_url(cik: str, accession: str, relative_name: str) -> str:
    safe_name = normalize_archive_relative_name(relative_name)
    return archive_root_url(cik, accession) + safe_name


def validate_archive_member_url(url: str) -> str:
    """Validate a package member URL without requiring package identity."""

    parsed = urlsplit(str(url).strip())
    if (
        parsed.scheme.casefold() != "https"
        or (parsed.hostname or "").casefold() != "www.sec.gov"
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
        or not parsed.path.startswith("/Archives/edgar/data/")
    ):
        raise SecError(P11Reason.P11_ARCHIVE_HOST_REJECTED, "SEC package member URL is not an archive URL")
    archive_path = parsed.path[len("/Archives/edgar/data/") :]
    if not archive_path or any(part in {"", ".", ".."} for part in archive_path.split("/")):
        raise SecError(P11Reason.P11_ARCHIVE_HOST_REJECTED, "SEC package member URL contains traversal")
    if "\\" in archive_path or unquote(archive_path) != archive_path or _DRIVE_RE.match(archive_path):
        raise SecError(P11Reason.P11_ARCHIVE_HOST_REJECTED, "SEC package member URL is not canonical")
    return str(url).strip()


def archive_url_is_exact(url: str, *, cik: str, accession: str, relative_name: str) -> bool:
    expected = archive_member_url(cik, accession, relative_name)
    return validate_archive_member_url(url) == expected


__all__ = [
    "archive_member_url",
    "archive_root_url",
    "archive_url_is_exact",
    "normalize_archive_relative_name",
    "validate_archive_member_url",
]
