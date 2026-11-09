from __future__ import annotations

from .errors import P11Reason, SecError
from .models import SecIssuerKind


class SecFormPolicy:
    @staticmethod
    def forms_for(period: str, issuer_kind: SecIssuerKind) -> tuple[str, ...]:
        normalized = period.strip().upper()
        if normalized not in {"Q1", "Q2", "Q3", "FY"}:
            raise ValueError(f"unsupported US period: {period!r}")
        if issuer_kind is SecIssuerKind.FPI:
            if normalized != "FY":
                raise SecError(
                    P11Reason.P11_UNSUPPORTED_FPI_PERIODIC_MAPPING,
                    "6-K is not automatically mapped to a US quarterly slot",
                )
            return ("20-F", "40-F")
        if normalized == "FY":
            return ("10-K",) if issuer_kind is SecIssuerKind.DOMESTIC else ("10-K", "20-F", "40-F")
        return ("10-Q",)

    @staticmethod
    def is_amendment(form: str) -> bool:
        return form.strip().upper().endswith("/A")

    @staticmethod
    def base_form(form: str) -> str:
        normalized = form.strip().upper()
        return normalized[:-2] if normalized.endswith("/A") else normalized
