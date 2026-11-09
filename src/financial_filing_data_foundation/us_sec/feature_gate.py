from __future__ import annotations

import os

from .errors import P11Reason, SecError


ENV_NAME = "FFDF_P11_US_DEV"


def is_us_development_enabled(env: dict[str, str] | None = None) -> bool:
    values = os.environ if env is None else env
    return values.get(ENV_NAME, "").strip() == "1"


def require_us_development(
    enabled: bool | None = None,
    *,
    env: dict[str, str] | None = None,
) -> None:
    allowed = is_us_development_enabled(env) if enabled is None else bool(enabled)
    if not allowed:
        raise SecError(
            P11Reason.P11_INVALID_US_IDENTITY,
            "US SEC provider is development-only; set FFDF_P11_US_DEV=1 explicitly",
        )
