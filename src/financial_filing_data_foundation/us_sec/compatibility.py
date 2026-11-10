from __future__ import annotations

from .parser import SEC_ARTIFACT_SCHEMA, VIRTUAL_HTML_NORMALIZER_VERSION


def sec_artifact_compatibility(*, parser_version: str, schema_version: str) -> str:
    """Return the persisted compatibility state for an SEC parse artifact."""

    if (
        str(parser_version) == VIRTUAL_HTML_NORMALIZER_VERSION
        and str(schema_version) == SEC_ARTIFACT_SCHEMA
    ):
        return "COMPATIBLE"
    return "INCOMPATIBLE"


__all__ = ["sec_artifact_compatibility"]
