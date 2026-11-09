from __future__ import annotations

import os
import threading
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from email.utils import parsedate_to_datetime
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import (
    HTTPRedirectHandler,
    Request,
    build_opener,
    urlopen,
)

from .errors import P11Reason, SecError


SEC_DATA_HOST = "data.sec.gov"
SEC_WWW_HOST = "www.sec.gov"
SEC_ALLOWED_HOSTS = frozenset({SEC_DATA_HOST, SEC_WWW_HOST})
SUBMISSIONS_MAX_BYTES = 32 * 1024 * 1024
MEMBER_MAX_BYTES = 128 * 1024 * 1024
PACKAGE_MAX_BYTES = 512 * 1024 * 1024
ERROR_BODY_MAX_BYTES = 1024 * 1024
_REDIRECT_CODES = frozenset({301, 302, 303, 307, 308})


def _allowed_path(host: str, path: str) -> bool:
    normalized = path or "/"
    if host == SEC_DATA_HOST:
        return normalized.startswith("/submissions/") or normalized.startswith(
            "/api/xbrl/"
        )
    return normalized.startswith("/Archives/") or normalized == "/files/company_tickers.json"


def validate_sec_url(url: str) -> str:
    """Validate and return an SEC URL before any network request is made."""

    if not isinstance(url, str) or not url.strip():
        raise SecError(P11Reason.P11_ARCHIVE_HOST_REJECTED, "SEC URL is required")
    parsed = urlparse(url.strip())
    host = (parsed.hostname or "").lower()
    if parsed.scheme.lower() != "https" or parsed.username or parsed.password:
        raise SecError(
            P11Reason.P11_ARCHIVE_HOST_REJECTED,
            "SEC requests require HTTPS without embedded credentials",
        )
    if host not in SEC_ALLOWED_HOSTS or not _allowed_path(host, parsed.path):
        raise SecError(
            P11Reason.P11_ARCHIVE_HOST_REJECTED,
            f"SEC URL is not allowlisted: {url}",
        )
    return url.strip()


@dataclass(frozen=True, slots=True)
class SecHttpConfig:
    contact_email: str
    application: str = "FFDF"
    organization: str = "FinancialFilingDataFoundation"
    rate_limit_per_second: float = 8.0
    max_attempts: int = 3
    timeout_seconds: float = 30.0
    max_redirects: int = 3
    submissions_max_bytes: int = SUBMISSIONS_MAX_BYTES
    member_max_bytes: int = MEMBER_MAX_BYTES

    @classmethod
    def from_env(cls) -> "SecHttpConfig":
        email = (
            os.environ.get("FFDF_SEC_CONTACT_EMAIL")
            or os.environ.get("SEC_CONTACT_EMAIL")
            or ""
        ).strip()
        if not email or "@" not in email:
            raise SecError(
                P11Reason.P11_INVALID_US_IDENTITY,
                "FFDF_SEC_CONTACT_EMAIL must be configured for SEC access",
            )
        return cls(contact_email=email)

    @property
    def user_agent(self) -> str:
        return f"{self.application}/{self.organization}; contact: {self.contact_email}"

    def __post_init__(self) -> None:
        if not self.contact_email.strip() or "@" not in self.contact_email:
            raise ValueError("contact_email must be a monitored email address")
        if self.rate_limit_per_second <= 0 or self.rate_limit_per_second >= 10:
            raise ValueError("rate_limit_per_second must be > 0 and < 10")
        if self.max_attempts < 1 or self.max_attempts > 5:
            raise ValueError("max_attempts must be between 1 and 5")
        if self.max_redirects < 0 or self.max_redirects > 5:
            raise ValueError("max_redirects must be between 0 and 5")


class SecRateLimiter:
    """Process-wide-compatible limiter; callers share the instance."""

    def __init__(
        self,
        rate_limit_per_second: float = 8.0,
        *,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        if rate_limit_per_second <= 0 or rate_limit_per_second >= 10:
            raise ValueError("rate_limit_per_second must be > 0 and < 10")
        self.interval = 1.0 / rate_limit_per_second
        self._clock = clock
        self._sleep = sleep
        self._lock = threading.Lock()
        self._last: float | None = None

    def wait(self) -> None:
        with self._lock:
            now = self._clock()
            if self._last is not None:
                remaining = self.interval - (now - self._last)
                if remaining > 0:
                    self._sleep(remaining)
                    now = self._clock()
            self._last = now


@dataclass(frozen=True, slots=True)
class SecResponse:
    status: int
    headers: Mapping[str, str]
    body: bytes
    final_url: str


Transport = Callable[[str, dict[str, str], float], SecResponse]


class _AllowlistedRedirectHandler(HTTPRedirectHandler):
    def __init__(self, *, max_redirects: int) -> None:
        super().__init__()
        if max_redirects < 0:
            raise ValueError("max_redirects must be non-negative")
        self.max_redirections = max_redirects

    def redirect_request(self, req: Request, fp: Any, code: int, msg: str, headers: Any, newurl: str) -> Request | None:
        validate_sec_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _network_transport(
    url: str,
    headers: dict[str, str],
    timeout: float,
    *,
    max_bytes: int = PACKAGE_MAX_BYTES,
    max_redirects: int = 3,
) -> SecResponse:
    if max_redirects < 0:
        raise ValueError("max_redirects must be non-negative")
    request = Request(url, headers=headers, method="GET")
    opener = build_opener(_AllowlistedRedirectHandler(max_redirects=max_redirects))
    try:
        with opener.open(request, timeout=timeout) as response:
            declared_length = response.headers.get("Content-Length")
            if declared_length:
                try:
                    if int(declared_length) > max_bytes:
                        raise SecError(
                            P11Reason.P11_SIZE_LIMIT_EXCEEDED,
                            f"SEC response exceeds {max_bytes} bytes",
                        )
                except ValueError:
                    pass
            chunks: list[bytes] = []
            remaining = max_bytes + 1
            while remaining > 0:
                chunk = response.read(min(1024 * 1024, remaining))
                if not chunk:
                    break
                chunks.append(chunk)
                remaining -= len(chunk)
            body = b"".join(chunks)
            if len(body) > max_bytes:
                raise SecError(
                    P11Reason.P11_SIZE_LIMIT_EXCEEDED,
                    f"SEC response exceeds {max_bytes} bytes",
                )
            return SecResponse(
                status=int(response.status),
                headers=dict(response.headers.items()),
                body=body,
                final_url=str(response.geturl()),
            )
    except HTTPError as exc:
        if int(exc.code) in _REDIRECT_CODES:
            raise SecError(
                P11Reason.P11_SEC_REDIRECT_LIMIT_EXCEEDED,
                f"SEC redirect limit exceeded after {max_redirects} hops",
            ) from exc
        error_limit = min(max_bytes, ERROR_BODY_MAX_BYTES)
        try:
            body = exc.read(error_limit + 1)
        except OSError:
            body = b""
        if len(body) > error_limit:
            raise SecError(
                P11Reason.P11_SIZE_LIMIT_EXCEEDED,
                f"SEC error response exceeds {error_limit} bytes",
            ) from exc
        return SecResponse(
            status=int(exc.code),
            headers=dict(exc.headers.items()) if exc.headers else {},
            body=body,
            final_url=str(exc.geturl() or url),
        )
    except (URLError, TimeoutError, OSError) as exc:
        raise SecError(
            P11Reason.P11_SEC_DISCOVERY_FAILED,
            f"SEC network request failed: {exc}",
            retryable=True,
        ) from exc


_DEFAULT_LIMITER: SecRateLimiter | None = None
_DEFAULT_LIMITER_LOCK = threading.Lock()


def _default_limiter(rate: float) -> SecRateLimiter:
    global _DEFAULT_LIMITER
    with _DEFAULT_LIMITER_LOCK:
        if _DEFAULT_LIMITER is None or abs(_DEFAULT_LIMITER.interval - 1.0 / rate) > 1e-12:
            _DEFAULT_LIMITER = SecRateLimiter(rate)
        return _DEFAULT_LIMITER


def _header(headers: Mapping[str, str], name: str) -> str | None:
    wanted = name.casefold()
    for key, value in headers.items():
        if str(key).casefold() == wanted:
            return str(value)
    return None


def _retry_after(headers: Mapping[str, str]) -> float | None:
    value = _header(headers, "Retry-After")
    if not value:
        return None
    try:
        seconds = float(value.strip())
        return max(0.0, min(seconds, 60.0))
    except ValueError:
        try:
            target = parsedate_to_datetime(value)
            return max(0.0, min(target.timestamp() - time.time(), 60.0))
        except (TypeError, ValueError, OverflowError):
            return None


def _content_type(headers: Mapping[str, str]) -> str:
    value = _header(headers, "Content-Type") or ""
    return value.split(";", 1)[0].strip().lower()


class SecHttpClient:
    def __init__(
        self,
        config: SecHttpConfig,
        *,
        transport: Transport | None = None,
        limiter: SecRateLimiter | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.config = config
        self.transport = transport or _network_transport
        self.limiter = limiter or _default_limiter(config.rate_limit_per_second)
        self.sleep = sleep

    def fetch(
        self,
        url: str,
        *,
        expected_content_types: tuple[str, ...] = (),
        max_bytes: int | None = None,
    ) -> SecResponse:
        validated_url = validate_sec_url(url)
        limit = max_bytes or self.config.member_max_bytes
        if limit <= 0:
            raise ValueError("max_bytes must be positive")
        last_status: int | None = None
        for attempt in range(self.config.max_attempts):
            self.limiter.wait()
            try:
                request_headers = {
                    "User-Agent": self.config.user_agent,
                }
                if self.transport is _network_transport:
                    response = _network_transport(
                        validated_url,
                        request_headers,
                        self.config.timeout_seconds,
                        max_bytes=limit,
                        max_redirects=self.config.max_redirects,
                    )
                elif hasattr(self.transport, "fetch"):
                    response = self.transport.fetch(  # type: ignore[attr-defined]
                        validated_url,
                        request_headers,
                        self.config.timeout_seconds,
                        max_bytes=limit,
                        max_redirects=self.config.max_redirects,
                    )
                else:
                    response = self.transport(
                        validated_url,
                        request_headers,
                        self.config.timeout_seconds,
                    )
            except SecError as exc:
                if not exc.retryable or attempt + 1 >= self.config.max_attempts:
                    raise
                self.sleep(min(2.0**attempt, 8.0))
                continue
            validate_sec_url(response.final_url)
            last_status = response.status
            if response.status == 200:
                content_encoding = _header(response.headers, "Content-Encoding")
                if content_encoding and content_encoding.strip().casefold() not in {"identity"}:
                    raise SecError(
                        P11Reason.P11_CONTENT_ENCODING_UNSUPPORTED,
                        f"unsupported SEC content encoding: {content_encoding}",
                    )
                if len(response.body) > limit:
                    raise SecError(
                        P11Reason.P11_SIZE_LIMIT_EXCEEDED,
                        f"SEC response exceeds {limit} bytes",
                    )
                if expected_content_types:
                    content_type = _content_type(response.headers)
                    if content_type not in {value.lower() for value in expected_content_types}:
                        raise SecError(
                            P11Reason.P11_CONTENT_TYPE_INVALID,
                            f"unexpected SEC content type: {content_type or '<missing>'}",
                        )
                return response

            if response.status in {403, 429}:
                if attempt + 1 >= self.config.max_attempts:
                    reason = (
                        P11Reason.P11_SEC_RATE_LIMITED
                        if response.status == 429
                        else P11Reason.P11_SEC_ACCESS_DENIED
                    )
                    raise SecError(reason, f"SEC returned HTTP {response.status}", retryable=True)
                delay = _retry_after(response.headers)
                if delay is None:
                    delay = min(2.0**attempt, 8.0)
                self.sleep(delay)
                continue

            if 500 <= response.status < 600 and attempt + 1 < self.config.max_attempts:
                self.sleep(min(2.0**attempt, 8.0))
                continue
            raise SecError(
                P11Reason.P11_SEC_DISCOVERY_FAILED,
                f"SEC returned HTTP {response.status}",
                retryable=bool(500 <= response.status < 600),
            )

        raise SecError(
            P11Reason.P11_SEC_DISCOVERY_FAILED,
            f"SEC request exhausted attempts (last status={last_status})",
            retryable=True,
        )


__all__ = [
    "MEMBER_MAX_BYTES",
    "PACKAGE_MAX_BYTES",
    "SEC_ALLOWED_HOSTS",
    "SUBMISSIONS_MAX_BYTES",
    "SecHttpClient",
    "SecHttpConfig",
    "SecRateLimiter",
    "SecResponse",
    "validate_sec_url",
]
