from __future__ import annotations

import datetime as dt
import hashlib
import http.client
import json
import os
import re
import socket
import ssl
import time
from pathlib import Path
from typing import Callable
from urllib.parse import SplitResult, urljoin, urlsplit

from .errors import SecHttpError
from .models import SecContentClass, SecHttpResponse
from .rate_gate import SecRateGate


_ALLOWED_HOSTS = frozenset({"data.sec.gov", "www.sec.gov", "sec.gov"})
_REDIRECT_STATUSES = frozenset({301, 302, 303, 307, 308})
_BACKOFF_SECONDS = (1.0, 2.0, 4.0)
_CAPS = {
    SecContentClass.TICKER_MAPPING_JSON: 16_777_216,
    SecContentClass.SUBMISSIONS_CURRENT_JSON: 33_554_432,
    SecContentClass.SUBMISSIONS_HISTORY_JSON: 16_777_216,
}
_CURRENT_PATH_RE = re.compile(r"^/submissions/CIK[0-9]{10}\.json$")
_INTEGER_RE = re.compile(r"^[0-9]+$")
_IMF_RE = re.compile(
    r"^(Mon|Tue|Wed|Thu|Fri|Sat|Sun), ([0-9]{2}) "
    r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) "
    r"([0-9]{4}) ([0-9]{2}):([0-9]{2}):([0-9]{2}) GMT$"
)
_MONTHS = {
    "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
    "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12,
}
_WEEKDAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")


def _http_error(reason_code: str, message: str) -> SecHttpError:
    return SecHttpError(reason_code, message)


def _validate_user_agent(value: str | None) -> tuple[str, str]:
    if value is None or not value.isascii():
        raise _http_error("P11_USER_AGENT_REQUIRED", "SEC_USER_AGENT is missing or invalid")
    data = value.encode("ascii")
    if not 8 <= len(data) <= 256:
        raise _http_error("P11_USER_AGENT_REQUIRED", "SEC_USER_AGENT is missing or invalid")
    if value != value.strip(" \t\r\n\f\v") or any(not 0x20 <= ord(ch) <= 0x7E for ch in value):
        raise _http_error("P11_USER_AGENT_REQUIRED", "SEC_USER_AGENT is missing or invalid")
    tokens = value.split()
    if len(tokens) < 2:
        raise _http_error("P11_USER_AGENT_REQUIRED", "SEC_USER_AGENT is missing or invalid")
    if not any(token.count("@") == 1 and all(token.split("@")) for token in tokens):
        raise _http_error("P11_USER_AGENT_REQUIRED", "SEC_USER_AGENT is missing or invalid")
    return value, hashlib.sha256(data).hexdigest()


def _safe_history_basename(value: str) -> bool:
    return (
        bool(value)
        and value.endswith(".json")
        and all(0x21 <= ord(ch) <= 0x7E for ch in value)
        and value not in {".", ".."}
        and not any(ch in value for ch in "/\\%?#")
    )


def _validate_url(url: str, content_class: SecContentClass, *, redirect: bool) -> SplitResult:
    try:
        parsed = urlsplit(url)
        port = parsed.port
    except (TypeError, ValueError) as exc:
        reason = "P11_REDIRECT_NOT_ALLOWED" if redirect else "P11_SOURCE_HOST_NOT_ALLOWED"
        raise _http_error(reason, "invalid SEC URL") from exc
    reason = "P11_REDIRECT_NOT_ALLOWED" if redirect else "P11_SOURCE_HOST_NOT_ALLOWED"
    if parsed.scheme.lower() != "https" or parsed.username is not None or parsed.password is not None:
        raise _http_error(reason, "SEC URL scheme or authority is not allowed")
    host = parsed.hostname
    if host is None or not host.isascii():
        raise _http_error(reason, "SEC URL host is not allowed")
    host = host.lower()
    if host.endswith(".") or host not in _ALLOWED_HOSTS or port not in (None, 443):
        raise _http_error(reason, "SEC URL host or port is not allowed")
    if parsed.fragment or parsed.query:
        raise _http_error(reason, "SEC URL query or fragment is not allowed")
    if "%" in parsed.path:
        raise _http_error(reason, "percent-encoded SEC path is not canonical")
    if content_class == SecContentClass.TICKER_MAPPING_JSON:
        path_ok = parsed.path == "/files/company_tickers.json"
        initial_host = "www.sec.gov"
    elif content_class == SecContentClass.SUBMISSIONS_CURRENT_JSON:
        path_ok = bool(_CURRENT_PATH_RE.fullmatch(parsed.path))
        initial_host = "data.sec.gov"
    elif content_class == SecContentClass.SUBMISSIONS_HISTORY_JSON:
        prefix = "/submissions/"
        name = parsed.path[len(prefix):] if parsed.path.startswith(prefix) else ""
        path_ok = parsed.path.startswith(prefix) and _safe_history_basename(name)
        initial_host = "data.sec.gov"
    else:  # pragma: no cover - runtime check below rejects non-enum values.
        path_ok = False
        initial_host = ""
    if not path_ok or (not redirect and host != initial_host):
        raise _http_error(reason, "SEC URL does not match the required content-class endpoint")
    return parsed


def _redirect_identity(parsed: SplitResult) -> tuple[str, str, int, str]:
    host = parsed.hostname
    if host is None:  # validated callers cannot reach this branch.
        raise _http_error("P11_REDIRECT_NOT_ALLOWED", "validated SEC URL is missing a host")
    return ("https", host.lower(), 443, parsed.path)


def _remaining_seconds(deadline_ns: int) -> float:
    remaining = (deadline_ns - time.monotonic_ns()) / 1_000_000_000
    if remaining <= 0:
        raise _http_error("P11_HTTP_FAILED", "logical SEC fetch deadline exceeded")
    return remaining


def _sleep_bounded(seconds: float, deadline_ns: int, *, rate_limited: bool = False) -> None:
    if seconds < 0:
        seconds = 0.0
    if time.monotonic_ns() + int(seconds * 1_000_000_000) > deadline_ns:
        reason = "P11_RATE_LIMITED" if rate_limited else "P11_HTTP_FAILED"
        raise _http_error(reason, "required wait exceeds logical SEC fetch deadline")
    end = time.monotonic() + seconds
    while True:
        remaining = end - time.monotonic()
        if remaining <= 0:
            return
        time.sleep(min(remaining, 0.05))


def _parse_imf_fixdate(value: str) -> float | None:
    match = _IMF_RE.fullmatch(value)
    if match is None:
        return None
    weekday, day_s, month_s, year_s, hour_s, minute_s, second_s = match.groups()
    try:
        when = dt.datetime(
            int(year_s), _MONTHS[month_s], int(day_s), int(hour_s), int(minute_s), int(second_s),
            tzinfo=dt.timezone.utc,
        )
    except ValueError:
        return None
    if _WEEKDAYS[when.weekday()] != weekday:
        return None
    return when.timestamp()


def _header_values(response: http.client.HTTPResponse, name: str) -> list[str]:
    values = response.headers.get_all(name, [])
    return [str(value) for value in values]


def _close_connection(response: http.client.HTTPResponse | None, connection: http.client.HTTPSConnection | None) -> None:
    if response is not None:
        try:
            response.close()
        except OSError:
            pass
    if connection is not None:
        try:
            connection.close()
        except OSError:
            pass


class SecHttpClient:
    def __init__(self, project_root: Path) -> None:
        root = Path(project_root).expanduser().resolve(strict=True)
        if not root.is_dir():
            raise ValueError("project_root must be an existing directory")
        self.project_root = root
        self._user_agent, self._user_agent_sha256 = _validate_user_agent(os.environ.get("SEC_USER_AGENT"))
        self._rate_gate = SecRateGate(root)

    @property
    def user_agent_sha256(self) -> str:
        return self._user_agent_sha256

    def _prepare_connection(self, parsed: SplitResult, deadline_ns: int) -> http.client.HTTPSConnection:
        timeout = min(10.0, _remaining_seconds(deadline_ns))
        context = ssl.create_default_context()
        connection = http.client.HTTPSConnection(parsed.hostname, port=443, timeout=timeout, context=context)
        connection.connect()
        return connection

    def _send_request(
        self,
        connection: http.client.HTTPSConnection,
        parsed: SplitResult,
        deadline_ns: int,
        on_start: Callable[[], None],
    ) -> None:
        def send() -> None:
            remaining = _remaining_seconds(deadline_ns)
            if connection.sock is None:
                raise OSError("HTTPS connection socket is unavailable")
            connection.sock.settimeout(min(10.0, remaining))
            connection.putrequest("GET", parsed.path, skip_host=True, skip_accept_encoding=True)
            connection.putheader("Host", parsed.hostname)
            connection.putheader("User-Agent", self._user_agent)
            connection.putheader("Accept", "application/json")
            connection.putheader("Accept-Encoding", "identity")
            connection.endheaders()

        self._rate_gate.emit(send, on_start, deadline_ns)

    @staticmethod
    def _transport_retryable(exc: BaseException) -> bool:
        return isinstance(exc, (TimeoutError, socket.timeout, ConnectionResetError, ConnectionAbortedError))

    def _schedule_retry(
        self,
        retry_count: int,
        deadline_ns: int,
        *,
        retry_after_values: list[str] | None = None,
    ) -> int:
        is_429 = retry_after_values is not None
        if retry_count >= 3:
            reason = "P11_RATE_LIMITED" if is_429 else "P11_HTTP_FAILED"
            raise _http_error(reason, "SEC retry limit exhausted")
        next_count = retry_count + 1
        wait_seconds = _BACKOFF_SECONDS[next_count - 1]
        if retry_after_values is not None:
            if len(retry_after_values) > 1:
                raise _http_error("P11_RATE_LIMITED", "multiple Retry-After fields are ambiguous")
            if len(retry_after_values) == 1:
                value = retry_after_values[0].strip(" \t")
                parsed_wait: float | None = None
                if _INTEGER_RE.fullmatch(value):
                    significant = value.lstrip("0") or "0"
                    if len(significant) > 2 or int(significant) > 60:
                        raise _http_error("P11_RATE_LIMITED", "Retry-After wait exceeds 60 seconds")
                    parsed_wait = float(int(significant))
                else:
                    timestamp = _parse_imf_fixdate(value)
                    if timestamp is not None:
                        parsed_wait = max(0.0, timestamp - time.time())
                if parsed_wait is not None:
                    wait_seconds = max(wait_seconds, parsed_wait)
                    if wait_seconds > 60.0:
                        raise _http_error("P11_RATE_LIMITED", "Retry-After wait exceeds 60 seconds")
        _sleep_bounded(wait_seconds, deadline_ns, rate_limited=is_429)
        return next_count

    @staticmethod
    def _validate_success_headers(
        response: http.client.HTTPResponse,
        content_class: SecContentClass,
    ) -> tuple[bool, int | None, int]:
        transfer = _header_values(response, "Transfer-Encoding")
        lengths = _header_values(response, "Content-Length")
        content_types = _header_values(response, "Content-Type")
        encodings = _header_values(response, "Content-Encoding")
        if len(transfer) > 1 or len(lengths) > 1:
            raise _http_error("P11_HTTP_FAILED", "ambiguous HTTP response framing headers")
        chunked = False
        if transfer:
            if transfer[0].strip(" \t").lower() != "chunked":
                raise _http_error("P11_HTTP_FAILED", "unsupported Transfer-Encoding")
            chunked = True
        if transfer and lengths:
            raise _http_error("P11_HTTP_FAILED", "Transfer-Encoding and Content-Length must not coexist")
        declared_length: int | None = None
        if lengths:
            value = lengths[0].strip(" \t")
            if not value.isascii() or _INTEGER_RE.fullmatch(value) is None:
                raise _http_error("P11_HTTP_FAILED", "invalid Content-Length")
            declared_length = int(value)
        if len(content_types) != 1 or content_types[0].strip(" \t").lower() != "application/json":
            raise _http_error("P11_CONTENT_TYPE_INVALID", "SEC JSON response Content-Type is invalid")
        if len(encodings) > 1 or (encodings and encodings[0].strip(" \t").lower() != "identity"):
            raise _http_error("P11_HTTP_FAILED", "SEC JSON Content-Encoding is invalid")
        cap = _CAPS[content_class]
        if declared_length is not None and declared_length > cap:
            raise _http_error("P11_RESPONSE_TOO_LARGE", "SEC JSON response exceeds size cap")
        return chunked, declared_length, cap

    @staticmethod
    def _read_body(
        response: http.client.HTTPResponse,
        connection: http.client.HTTPSConnection,
        *,
        chunked: bool,
        declared_length: int | None,
        cap: int,
        deadline_ns: int,
    ) -> bytes:
        parts: list[bytes] = []
        total = 0
        while True:
            remaining = _remaining_seconds(deadline_ns)
            if connection.sock is not None:
                connection.sock.settimeout(min(30.0, remaining))
            to_read = min(65_536, cap + 1 - total)
            if to_read <= 0:
                raise _http_error("P11_RESPONSE_TOO_LARGE", "SEC JSON response exceeds size cap")
            data = response.read(to_read)
            if not data:
                break
            total += len(data)
            if total > cap:
                raise _http_error("P11_RESPONSE_TOO_LARGE", "SEC JSON response exceeds size cap")
            parts.append(data)
        if not chunked and declared_length is not None and total != declared_length:
            raise _http_error("P11_HTTP_FAILED", "SEC JSON Content-Length does not match entity bytes")
        return b"".join(parts)

    @staticmethod
    def _validate_json_bytes(body: bytes) -> None:
        if body.startswith(b"\xef\xbb\xbf"):
            raise _http_error("P11_HTTP_FAILED", "SEC JSON UTF-8 BOM is not allowed")
        try:
            text = body.decode("utf-8", errors="strict")
            json.loads(text)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise _http_error("P11_HTTP_FAILED", "SEC response is not valid strict UTF-8 JSON") from exc

    def get_json(self, url: str, content_class: SecContentClass) -> SecHttpResponse:
        deadline_ns = time.monotonic_ns() + 120_000_000_000
        if not isinstance(content_class, SecContentClass):
            raise ValueError("content_class must be SecContentClass")
        requested_url = str(url)
        current_url = requested_url
        parsed = _validate_url(current_url, content_class, redirect=False)
        retry_count = 0
        redirect_count = 0
        outbound_start_count = 0
        visited = {_redirect_identity(parsed)}
        while True:
            if outbound_start_count >= 7:
                raise _http_error(
                    "P11_HTTP_FAILED",
                    "SEC outbound request-start invariant exhausted",
                )
            connection: http.client.HTTPSConnection | None = None
            response: http.client.HTTPResponse | None = None
            try:
                connection = self._prepare_connection(parsed, deadline_ns)
                def on_start() -> None:
                    nonlocal outbound_start_count
                    outbound_start_count += 1
                self._send_request(connection, parsed, deadline_ns, on_start)
                if connection.sock is not None:
                    connection.sock.settimeout(min(30.0, _remaining_seconds(deadline_ns)))
                response = connection.getresponse()
            except SecHttpError:
                _close_connection(response, connection)
                raise
            except (socket.gaierror, ssl.CertificateError, ssl.SSLCertVerificationError, ssl.SSLError) as exc:
                _close_connection(response, connection)
                raise _http_error("P11_HTTP_FAILED", "SEC connection preparation failed") from exc
            except BaseException as exc:
                _close_connection(response, connection)
                if self._transport_retryable(exc):
                    retry_count = self._schedule_retry(retry_count, deadline_ns)
                    continue
                raise _http_error("P11_HTTP_FAILED", "SEC HTTP transport failed") from exc

            status = response.status
            if status in _REDIRECT_STATUSES:
                locations = _header_values(response, "Location")
                _close_connection(response, connection)
                if len(locations) != 1 or not locations[0].strip(" \t"):
                    raise _http_error("P11_REDIRECT_NOT_ALLOWED", "SEC redirect Location is missing or ambiguous")
                if redirect_count >= 3:
                    raise _http_error("P11_REDIRECT_NOT_ALLOWED", "SEC redirect limit exceeded")
                next_url = urljoin(current_url, locations[0].strip(" \t"))
                next_parsed = _validate_url(next_url, content_class, redirect=True)
                next_identity = _redirect_identity(next_parsed)
                if next_identity in visited:
                    raise _http_error("P11_REDIRECT_NOT_ALLOWED", "SEC redirect loop detected")
                visited.add(next_identity)
                redirect_count += 1
                current_url = next_url
                parsed = next_parsed
                continue

            if status == 429:
                retry_after = _header_values(response, "Retry-After")
                _close_connection(response, connection)
                retry_count = self._schedule_retry(
                    retry_count,
                    deadline_ns,
                    retry_after_values=retry_after,
                )
                continue

            if 500 <= status <= 599:
                _close_connection(response, connection)
                retry_count = self._schedule_retry(retry_count, deadline_ns)
                continue

            if status != 200:
                _close_connection(response, connection)
                raise _http_error("P11_HTTP_FAILED", f"SEC HTTP status {status} is not accepted")

            try:
                chunked, declared_length, cap = self._validate_success_headers(response, content_class)
                body = self._read_body(
                    response,
                    connection,
                    chunked=chunked,
                    declared_length=declared_length,
                    cap=cap,
                    deadline_ns=deadline_ns,
                )
                self._validate_json_bytes(body)
            except SecHttpError:
                _close_connection(response, connection)
                raise
            except BaseException as exc:
                _close_connection(response, connection)
                if self._transport_retryable(exc):
                    retry_count = self._schedule_retry(retry_count, deadline_ns)
                    continue
                raise _http_error("P11_HTTP_FAILED", "SEC HTTP response read failed") from exc
            _close_connection(response, connection)
            return SecHttpResponse(
                requested_url=requested_url,
                final_url=current_url,
                status=200,
                content_type="application/json",
                body=body,
                outbound_start_count=outbound_start_count,
                redirect_count=redirect_count,
            )