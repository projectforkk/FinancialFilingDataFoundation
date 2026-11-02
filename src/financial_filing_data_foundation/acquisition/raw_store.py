from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

from financial_filing_data_foundation.acquisition.dayu_protocol import atomic_write_json
from financial_filing_data_foundation.acquisition.models import (
    AcquisitionError,
    AcquisitionReason,
    AcquisitionReceiptRef,
    RawStoredDocument,
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


class RawDocumentStore:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).expanduser().resolve()
        self.sha_root = self.root / "sha256"
        self.receipt_root = self.root / "receipts"
        self.staging_root = self.root / "staging"
        for path in (self.sha_root, self.receipt_root, self.staging_root):
            path.mkdir(parents=True, exist_ok=True)

    def new_staging_path(self, prefix: str = "acq-") -> Path:
        handle = tempfile.NamedTemporaryFile(
            prefix=prefix,
            suffix=".pdf",
            dir=self.staging_root,
            delete=False,
        )
        path = Path(handle.name).resolve()
        handle.close()
        return path

    def validate_staging_pdf(
        self,
        staging_path: str | Path,
        expected_sha256: str | None = None,
        expected_size: int | None = None,
    ) -> tuple[str, int]:
        path = Path(staging_path).expanduser().resolve()
        if not _is_within(path, self.staging_root):
            raise AcquisitionError(
                AcquisitionReason.STAGING_WRITE_FAILED,
                f"staging path outside raw-store staging root: {path}",
            )
        if not path.is_file():
            raise AcquisitionError(
                AcquisitionReason.STAGING_WRITE_FAILED,
                f"staging PDF not found: {path}",
            )

        before = path.stat()
        if before.st_size < 5:
            raise AcquisitionError(
                AcquisitionReason.PDF_VALIDATION_FAILED,
                f"staging PDF is too small: {before.st_size}",
            )
        with path.open("rb") as handle:
            magic = handle.read(5)
        if magic != b"%PDF-":
            raise AcquisitionError(
                AcquisitionReason.PDF_VALIDATION_FAILED,
                "staging file does not start with PDF magic",
            )

        actual_sha = sha256_file(path)
        after = path.stat()
        if (
            before.st_size != after.st_size
            or before.st_mtime_ns != after.st_mtime_ns
        ):
            raise AcquisitionError(
                AcquisitionReason.PDF_VALIDATION_FAILED,
                "staging file changed during validation",
            )

        if expected_size is not None and after.st_size != expected_size:
            raise AcquisitionError(
                AcquisitionReason.SHA_MISMATCH,
                f"staging size {after.st_size} != runner size {expected_size}",
            )
        if expected_sha256 is not None and actual_sha.lower() != expected_sha256.lower():
            raise AcquisitionError(
                AcquisitionReason.SHA_MISMATCH,
                f"FFDF SHA {actual_sha} != runner SHA {expected_sha256}",
            )
        return actual_sha, after.st_size

    def commit_staging(
        self,
        staging_path: str | Path,
        document_sha256: str,
    ) -> RawStoredDocument:
        staging = Path(staging_path).expanduser().resolve()
        sha = document_sha256.lower()
        if len(sha) != 64 or any(ch not in "0123456789abcdef" for ch in sha):
            raise AcquisitionError(
                AcquisitionReason.RAW_STORE_FAILED,
                f"invalid SHA256: {document_sha256}",
            )
        if not _is_within(staging, self.staging_root):
            raise AcquisitionError(
                AcquisitionReason.STAGING_WRITE_FAILED,
                f"staging path outside raw-store staging root: {staging}",
            )
        if not staging.is_file():
            raise AcquisitionError(
                AcquisitionReason.STAGING_WRITE_FAILED,
                f"staging file missing: {staging}",
            )

        final_dir = self.sha_root / sha[:2]
        final_dir.mkdir(parents=True, exist_ok=True)
        final_path = (final_dir / f"{sha}.pdf").resolve()
        if not _is_within(final_path, self.sha_root):
            raise AcquisitionError(
                AcquisitionReason.RAW_STORE_FAILED,
                "computed final path escaped raw store",
            )

        if final_path.exists():
            existing_sha = sha256_file(final_path)
            if existing_sha != sha:
                raise AcquisitionError(
                    AcquisitionReason.RAW_STORE_CORRUPTION,
                    f"existing raw object hash mismatch: {final_path}",
                )
            existing_size = final_path.stat().st_size
            staging.unlink()
            return RawStoredDocument(
                document_sha256=sha,
                path=final_path,
                file_size=existing_size,
                reused_existing=True,
            )

        os.replace(staging, final_path)
        committed_sha = sha256_file(final_path)
        if committed_sha != sha:
            raise AcquisitionError(
                AcquisitionReason.RAW_STORE_CORRUPTION,
                f"committed raw object hash mismatch: {final_path}",
            )
        return RawStoredDocument(
            document_sha256=sha,
            path=final_path,
            file_size=final_path.stat().st_size,
            reused_existing=False,
        )

    @staticmethod
    def receipt_id(provider: str, source_id: str, document_sha256: str) -> str:
        raw = (
            provider.encode("utf-8")
            + b"\0"
            + source_id.encode("utf-8")
            + b"\0"
            + document_sha256.lower().encode("ascii")
        )
        return hashlib.sha256(raw).hexdigest()

    def write_receipt(self, payload: dict[str, Any]) -> AcquisitionReceiptRef:
        provider = str(payload["provider"])
        source_id = str(payload["source_id"])
        document_sha256 = str(payload["document_sha256"]).lower()
        receipt_id = self.receipt_id(provider, source_id, document_sha256)
        receipt_dir = self.receipt_root / receipt_id[:2]
        receipt_dir.mkdir(parents=True, exist_ok=True)
        receipt_path = (receipt_dir / f"{receipt_id}.json").resolve()

        canonical = dict(payload)
        canonical["receipt_id"] = receipt_id
        if receipt_path.exists():
            existing = json.loads(receipt_path.read_text(encoding="utf-8"))
            if existing != canonical:
                raise AcquisitionError(
                    AcquisitionReason.RAW_STORE_FAILED,
                    f"receipt id collision with different semantic content: {receipt_id}",
                )
            return AcquisitionReceiptRef(receipt_id=receipt_id, path=receipt_path)

        atomic_write_json(receipt_path, canonical)
        return AcquisitionReceiptRef(receipt_id=receipt_id, path=receipt_path)
