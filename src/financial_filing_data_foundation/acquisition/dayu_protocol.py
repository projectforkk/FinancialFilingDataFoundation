from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from financial_filing_data_foundation.acquisition.models import (
    AcquisitionCandidate,
    DiscoveryResult,
    ProviderCompanyProfile,
    RunnerDownloadedAsset,
)


def atomic_write_json(path: str | Path, payload: dict[str, Any]) -> Path:
    output = Path(path).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(output.name + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, output)
    return output


def read_json_object(path: str | Path) -> dict[str, Any]:
    source = Path(path).expanduser().resolve()
    payload = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("protocol JSON root must be an object")
    return payload


def candidate_to_dict(candidate: AcquisitionCandidate) -> dict[str, Any]:
    return {
        "provider": candidate.provider,
        "provider_company_id": candidate.provider_company_id,
        "provider_company_name": candidate.provider_company_name,
        "ticker": candidate.ticker,
        "source_id": candidate.source_id,
        "source_url": candidate.source_url,
        "source_title": candidate.source_title,
        "language": candidate.language,
        "filing_date": candidate.filing_date,
        "fiscal_year": candidate.fiscal_year,
        "fiscal_period": candidate.fiscal_period,
        "amended": candidate.amended,
        "remote_content_length": candidate.remote_content_length,
        "etag": candidate.etag,
        "last_modified": candidate.last_modified,
    }


def candidate_from_dict(payload: dict[str, Any]) -> AcquisitionCandidate:
    return AcquisitionCandidate(
        provider=str(payload["provider"]),
        provider_company_id=str(payload["provider_company_id"]),
        provider_company_name=str(payload.get("provider_company_name") or ""),
        ticker=str(payload["ticker"]),
        source_id=str(payload["source_id"]),
        source_url=str(payload["source_url"]),
        source_title=str(payload["source_title"]),
        language=str(payload["language"]),
        filing_date=str(payload["filing_date"]),
        fiscal_year=int(payload["fiscal_year"]),
        fiscal_period=str(payload["fiscal_period"]),
        amended=bool(payload["amended"]),
        remote_content_length=(
            None
            if payload.get("remote_content_length") is None
            else int(payload["remote_content_length"])
        ),
        etag=None if payload.get("etag") is None else str(payload["etag"]),
        last_modified=(
            None if payload.get("last_modified") is None else str(payload["last_modified"])
        ),
    )


def discovery_from_response(payload: dict[str, Any]) -> DiscoveryResult:
    profile_payload = payload["profile"]
    if not isinstance(profile_payload, dict):
        raise ValueError("profile must be an object")
    candidate_payloads = payload["candidates"]
    if not isinstance(candidate_payloads, list):
        raise ValueError("candidates must be a list")
    profile = ProviderCompanyProfile(
        provider=str(profile_payload["provider"]),
        company_id=str(profile_payload["company_id"]),
        company_name=str(profile_payload["company_name"]),
        ticker=str(profile_payload["ticker"]),
    )
    return DiscoveryResult(
        profile=profile,
        candidates=tuple(
            candidate_from_dict(item)
            for item in candidate_payloads
            if isinstance(item, dict)
        ),
    )


def downloaded_asset_from_response(payload: dict[str, Any]) -> RunnerDownloadedAsset:
    candidate_payload = payload["candidate"]
    if not isinstance(candidate_payload, dict):
        raise ValueError("candidate must be an object")
    return RunnerDownloadedAsset(
        candidate=candidate_from_dict(candidate_payload),
        staging_path=Path(str(payload["staging_path"])).expanduser().resolve(),
        sha256=str(payload["dayu_temp_sha256"]).lower(),
        content_length=int(payload["dayu_content_length"]),
        downloaded_at=str(payload["downloaded_at"]),
        request_id=str(payload["request_id"]),
        runner_version=str(payload["runner_version"]),
    )
