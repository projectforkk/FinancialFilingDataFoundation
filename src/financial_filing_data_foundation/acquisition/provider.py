from __future__ import annotations

from pathlib import Path
from typing import Protocol

from financial_filing_data_foundation.acquisition.models import (
    AcquisitionCandidate,
    AcquisitionRequest,
    DiscoveryResult,
    RunnerDownloadedAsset,
)
from financial_filing_data_foundation.identity import SourceMetadata


class AcquisitionProvider(Protocol):
    name: str

    def discover_documents(self, request: AcquisitionRequest) -> DiscoveryResult: ...

    def download_document(
        self,
        candidate: AcquisitionCandidate,
        staging_path: Path,
    ) -> RunnerDownloadedAsset: ...

    def source_metadata(
        self,
        candidate: AcquisitionCandidate,
        downloaded_at: str,
    ) -> SourceMetadata: ...
