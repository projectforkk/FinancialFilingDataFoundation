from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

from financial_filing_data_foundation.acquisition.models import (
    AcquisitionCandidate,
    AcquisitionError,
    AcquisitionReason,
    AcquisitionRequest,
    AcquisitionResult,
    AcquisitionStatus,
    DAYU_PACKAGE_VERSION,
    DAYU_PINNED_COMMIT,
    DAYU_REPOSITORY,
    PROTOCOL_VERSION,
)
from financial_filing_data_foundation.acquisition.provider import AcquisitionProvider
from financial_filing_data_foundation.acquisition.raw_store import RawDocumentStore
from financial_filing_data_foundation.identity import FilingIdentity
from financial_filing_data_foundation.registry import (
    LocalDocumentStatus,
    SQLiteRegistry,
)


_EXPECTED_PROVIDER = {
    "CN": "cninfo",
    "HK": "hkexnews",
}

_ALLOWED_HOSTS = {
    "CN": frozenset(
        {
            "www.cninfo.com.cn",
            "cninfo.com.cn",
            "static.cninfo.com.cn",
        }
    ),
    "HK": frozenset(
        {
            "www1.hkexnews.hk",
            "hkexnews.hk",
        }
    ),
}


def _validate_source_url(market: str, source_url: str) -> None:
    parsed = urlparse(source_url)
    host = (parsed.hostname or "").lower()
    if host not in _ALLOWED_HOSTS[market]:
        raise AcquisitionError(
            AcquisitionReason.SOURCE_HOST_NOT_ALLOWED,
            f"source host not allowed for {market}: {host or '<missing>'}",
        )
    if market == "HK" and parsed.scheme.lower() != "https":
        raise AcquisitionError(
            AcquisitionReason.SOURCE_HOST_NOT_ALLOWED,
            f"HKEX source must use https: {source_url}",
        )
    if market == "CN" and parsed.scheme.lower() not in {"http", "https"}:
        raise AcquisitionError(
            AcquisitionReason.SOURCE_HOST_NOT_ALLOWED,
            f"CNINFO source must use http/https: {source_url}",
        )


def _candidate_critical_metadata(candidate: AcquisitionCandidate) -> tuple[object, ...]:
    return (
        candidate.provider_company_id,
        candidate.source_title,
        candidate.language,
        candidate.filing_date,
        candidate.fiscal_year,
        candidate.fiscal_period,
        candidate.amended,
        candidate.remote_content_length,
        candidate.etag,
        candidate.last_modified,
    )


def _exact_candidates(
    request: AcquisitionRequest,
    candidates: tuple[AcquisitionCandidate, ...],
) -> tuple[tuple[AcquisitionCandidate, ...], bool]:
    expected_provider = _EXPECTED_PROVIDER[request.slot.market]
    matches: list[AcquisitionCandidate] = []
    for candidate in candidates:
        if candidate.provider != expected_provider:
            continue
        if candidate.ticker != request.company.ticker:
            continue
        if candidate.fiscal_year != request.slot.fiscal_year:
            continue
        if candidate.fiscal_period != request.slot.raw_fiscal_period:
            continue
        _validate_source_url(request.slot.market, candidate.source_url)
        matches.append(candidate)

    by_identity: dict[tuple[str, str], list[AcquisitionCandidate]] = {}
    for candidate in matches:
        by_identity.setdefault(
            (candidate.source_id, candidate.source_url), []
        ).append(candidate)

    deduplicated: list[AcquisitionCandidate] = []
    for key in sorted(by_identity, key=lambda item: (item[0], item[1])):
        group = by_identity[key]
        signatures = {_candidate_critical_metadata(candidate) for candidate in group}
        if len(signatures) > 1:
            return (), True
        deduplicated.append(
            sorted(
                group,
                key=lambda candidate: (
                    candidate.provider_company_name,
                    candidate.source_title,
                    candidate.language,
                ),
            )[0]
        )
    return tuple(deduplicated), False


def acquire_slot(
    request: AcquisitionRequest,
    provider: AcquisitionProvider,
    raw_store: RawDocumentStore,
    registry: SQLiteRegistry,
) -> AcquisitionResult:
    local = registry.resolve_local_document(request.slot)
    if local.status == LocalDocumentStatus.RESOLVED:
        return AcquisitionResult(
            status=AcquisitionStatus.REUSED_LOCAL,
            reason_code=AcquisitionReason.LOCAL_RAW_ALREADY_AVAILABLE.value,
            slot=request.slot,
            document_sha256=local.document_sha256,
            raw_path=local.canonical_path,
        )
    if local.status == LocalDocumentStatus.AMBIGUOUS:
        return AcquisitionResult(
            status=AcquisitionStatus.REVIEW_REQUIRED,
            reason_code=AcquisitionReason.LOCAL_STATE_AMBIGUOUS.value,
            slot=request.slot,
        )
    if local.status == LocalDocumentStatus.CONFLICT:
        return AcquisitionResult(
            status=AcquisitionStatus.BLOCKED,
            reason_code=AcquisitionReason.LOCAL_STATE_CONFLICT.value,
            slot=request.slot,
        )
    if local.status == LocalDocumentStatus.DRIFTED:
        return AcquisitionResult(
            status=AcquisitionStatus.BLOCKED,
            reason_code=AcquisitionReason.LOCAL_CONTENT_DRIFT.value,
            slot=request.slot,
        )

    discovery = provider.discover_documents(request)
    expected_provider = _EXPECTED_PROVIDER[request.slot.market]
    if discovery.profile.provider != expected_provider:
        raise AcquisitionError(
            AcquisitionReason.DISCOVERY_FAILED,
            f"provider profile mismatch: {discovery.profile.provider}",
        )
    if discovery.profile.ticker != request.company.ticker:
        raise AcquisitionError(
            AcquisitionReason.DISCOVERY_FAILED,
            f"provider profile ticker mismatch: {discovery.profile.ticker}",
        )

    candidates, metadata_conflict = _exact_candidates(
        request, discovery.candidates
    )
    if metadata_conflict:
        return AcquisitionResult(
            status=AcquisitionStatus.REVIEW_REQUIRED,
            reason_code=(
                AcquisitionReason.ACQUISITION_CANDIDATE_METADATA_CONFLICT.value
            ),
            slot=request.slot,
            provider=expected_provider,
        )
    if not candidates:
        return AcquisitionResult(
            status=AcquisitionStatus.NOT_FOUND,
            reason_code=AcquisitionReason.NO_CANDIDATE.value,
            slot=request.slot,
            provider=expected_provider,
        )
    if len(candidates) > 1:
        return AcquisitionResult(
            status=AcquisitionStatus.REVIEW_REQUIRED,
            reason_code=AcquisitionReason.ACQUISITION_CANDIDATE_AMBIGUOUS.value,
            slot=request.slot,
            provider=expected_provider,
        )

    candidate = candidates[0]
    staging_path = raw_store.new_staging_path(
        prefix=f"{request.company.ticker}-{request.slot.fiscal_year}-"
    )
    try:
        asset = provider.download_document(candidate, staging_path)
        if asset.candidate != candidate:
            raise AcquisitionError(
                AcquisitionReason.RUNNER_PROTOCOL_INVALID,
                "download response candidate differs from selected candidate",
            )
        if asset.staging_path.resolve() != staging_path.resolve():
            raise AcquisitionError(
                AcquisitionReason.STAGING_WRITE_FAILED,
                "runner returned a different staging path",
            )

        ffdf_sha, ffdf_size = raw_store.validate_staging_pdf(
            staging_path,
            expected_sha256=asset.sha256,
            expected_size=asset.content_length,
        )
        stored = raw_store.commit_staging(staging_path, ffdf_sha)
    except Exception:
        if staging_path.exists():
            try:
                staging_path.unlink()
            except OSError:
                pass
        raise

    source = provider.source_metadata(candidate, asset.downloaded_at)
    try:
        registered = registry.register_document(
            stored.path,
            source=source,
            expected_identity=FilingIdentity(
                slot=request.slot,
                amended=candidate.amended,
            ),
        )
    except Exception as exc:
        raise AcquisitionError(
            AcquisitionReason.REGISTRY_FAILED,
            f"registry registration failed: {exc}",
        ) from exc

    if registered.document_sha256 != stored.document_sha256:
        raise AcquisitionError(
            AcquisitionReason.REGISTRY_FAILED,
            "registry SHA differs from raw-store SHA",
        )

    runtime = getattr(provider, "runtime", None)
    runtime_payload = runtime.to_dict() if runtime is not None else None
    receipt_payload = {
        "protocol_version": PROTOCOL_VERSION,
        "market": request.slot.market,
        "ticker": request.company.ticker,
        "filing_slot": request.slot.serialize(),
        "provider": candidate.provider,
        "provider_company_id": candidate.provider_company_id,
        "provider_company_name": candidate.provider_company_name,
        "source_id": candidate.source_id,
        "source_url": candidate.source_url,
        "source_title": candidate.source_title,
        "language": candidate.language,
        "filing_date": candidate.filing_date,
        "fiscal_year": candidate.fiscal_year,
        "fiscal_period": candidate.fiscal_period,
        "amended": candidate.amended,
        "etag": candidate.etag,
        "last_modified": candidate.last_modified,
        "remote_content_length": candidate.remote_content_length,
        "dayu_repository": (
            runtime.dayu_repository if runtime is not None else DAYU_REPOSITORY
        ),
        "dayu_pinned_commit": (
            runtime.dayu_commit if runtime is not None else DAYU_PINNED_COMMIT
        ),
        "dayu_package_version": (
            runtime.dayu_package_version
            if runtime is not None
            else DAYU_PACKAGE_VERSION
        ),
        "dayu_runtime": runtime_payload,
        "runner_version": asset.runner_version,
        "request_id": asset.request_id,
        "dayu_reported_sha256": asset.sha256,
        "document_sha256": stored.document_sha256,
        "ffdf_recomputed_sha256": ffdf_sha,
        "final_file_size": stored.file_size,
        "final_raw_path": str(stored.path),
        "downloaded_at": asset.downloaded_at,
        "registry_result": {
            "document_sha256": registered.document_sha256,
            "path": str(registered.path),
            "binding_status": (
                None
                if registered.binding_status is None
                else registered.binding_status.value
            ),
        },
        "raw_store_reused_existing": stored.reused_existing,
        "docling_conversion_used": False,
    }
    receipt = raw_store.write_receipt(receipt_payload)

    return AcquisitionResult(
        status=AcquisitionStatus.DOWNLOADED,
        reason_code=AcquisitionReason.ACQUISITION_COMPLETE.value,
        slot=request.slot,
        document_sha256=stored.document_sha256,
        raw_path=stored.path,
        receipt_path=receipt.path,
        source_id=candidate.source_id,
        provider=candidate.provider,
    )
