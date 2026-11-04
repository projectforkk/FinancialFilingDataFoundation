# P11-D SEC HTTP / Discovery Contract

Status: **NORMATIVE AMENDED DESIGN — FRESH DETACHED REVIEW REQUIRED / P11-D IMPLEMENTATION NOT AUTHORIZED**

Phase:
P11 — US SEC Provider / P11-D

Authorization:
`development/212-p11-d-http-discovery-design-freeze-authorization.md`

This document freezes the exact HTTP, rate-gate and Submissions-discovery contract required before any P11-D production code may be authorized.

If a P11-D HTTP/discovery detail conflicts with older general wording in `design/26-p11-sec-provider-design.md` or `design/27-p11-implementation-plan.md`, this document controls for P11-D only. P11-A/B/C accepted behavior remains immutable.

## 1. Scope

P11-D may later implement only:

- official SEC ticker mapping retrieval;
- official SEC Submissions current JSON retrieval;
- official SEC historical Submissions shard retrieval;
- strict HTTP/security/rate-limiting primitives required by those JSON endpoints;
- deterministic normalization/merge of current + historical discovery rows.

P11-D does **not** authorize:

- filing primary-document/package download;
- accession `index.json` package capture;
- XBRL/iXBRL parsing;
- package-store writes;
- registry writes;
- runtime-lock mutation;
- provider production.

Those remain later gates.

## 2. External SEC policy baseline

Current official SEC public guidance used for this freeze:

- scripted EDGAR access must declare a User-Agent;
- current aggregate public-access maximum = 10 requests/second;
- efficient scripting and moderated downloads are required.

The official policy source is `https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data`. Release/live acceptance MUST re-check the current official SEC guidance. If SEC lowers its applicable ceiling below FFDF's frozen 8 requests/second or materially changes automated-access requirements, P11 production is blocked until a new Design-First amendment is reviewed; FFDF MUST NOT rely on this historical 10 requests/second observation to override newer SEC policy.

Normative FFDF v1 policy is intentionally stricter:

- aggregate maximum = 8 outbound SEC request starts/second;
- no burst;
- minimum interval between actual outbound HTTP request starts = 125 ms;
- every retry and every redirect hop consumes a rate-gate reservation.

For rate verification, a rolling one-second window is the half-open interval `[t, t + 1 second)`. With starts separated by at least 125 ms, no such window may contain more than 8 starts.

## 3. Runtime / dependency boundary

P11-D must use Python standard-library networking only in v1.

The v1 transport boundary is standard-library `http.client.HTTPSConnection` (or an internal wrapper with exactly equivalent explicit connect / explicit header-send semantics). `urllib` automatic request dispatch/redirect handling is not permitted for production P11-D because the rate gate must control the actual HTTP header-send point.

No new HTTP dependency is authorized by P11-D.

The accepted P11-B project-local Python 3.12 AMD64 runtime remains the target SEC runtime. A future production runtime lock is separate; P11-D cannot silently change Arelle/lxml/runtime identities.

## 4. Public module surface

Later P11-D implementation must use:

```text
financial_filing_data_foundation.sec
```

Exact public exports:

```python
class SecHttpError(RuntimeError):
    def __init__(self, reason_code: str, message: str) -> None: ...

class SecDiscoveryError(RuntimeError):
    def __init__(self, reason_code: str, message: str) -> None: ...

class SecContentClass(StrEnum):
    TICKER_MAPPING_JSON = "TICKER_MAPPING_JSON"
    SUBMISSIONS_CURRENT_JSON = "SUBMISSIONS_CURRENT_JSON"
    SUBMISSIONS_HISTORY_JSON = "SUBMISSIONS_HISTORY_JSON"

@dataclass(frozen=True, slots=True)
class SecHttpResponse:
    requested_url: str
    final_url: str
    status: int
    content_type: str
    body: bytes
    outbound_start_count: int
    redirect_count: int

class SecHttpClient:
    def __init__(self, project_root: Path) -> None: ...
    def get_json(self, url: str, content_class: SecContentClass) -> SecHttpResponse: ...
```

Discovery exports:

```python
@dataclass(frozen=True, slots=True)
class SecDiscoveryCandidate:
    cik: str
    accession_number: str
    form: str
    base_form: str
    amended: bool
    filing_date: str
    report_date: str | None
    primary_document: str
    primary_doc_description: str | None
    is_xbrl: bool
    is_inline_xbrl: bool
    submission_source_urls: tuple[str, ...] = field(compare=False)


def load_sec_ticker_rows(client: SecHttpClient) -> tuple[tuple[str, str], ...]: ...


def discover_sec_filings(
    client: SecHttpClient,
    *,
    cik: str,
    target_base_forms: tuple[str, ...],
    filing_date_from: str,
    filing_date_to: str,
    target_accession: str | None = None,
) -> tuple[SecDiscoveryCandidate, ...]: ...
```

Both exception classes store the exact `reason_code` string on the instance and pass the exact `message` to `RuntimeError`; `str(exc)` therefore equals `message`. No raw User-Agent value may appear in an exception message.

`SecDiscoveryCandidate.submission_source_urls` requires `dataclasses.field(compare=False)`. It is provenance only: it is excluded from dataclass equality/hash, excluded from filing semantic identity, and excluded from every downstream package/parsed deterministic identity unless a later reviewed contract explicitly promotes a provenance field. `SecDiscoveryCandidate` intentionally has **no generated rich ordering**; all discovery ordering uses the explicit canonical key frozen in Section 17.

No caller-supplied arbitrary HTTP headers or User-Agent parameter exists in the public API.

### 4.1 Canonical project-root contract

`SecHttpClient(project_root)` requires the caller/orchestrator to pass the already configured **canonical FFDF project root**, following the existing FFDF explicit-project-root pattern. The client:

- converts it with `Path(project_root).expanduser().resolve(strict=True)`;
- requires the result to be a directory or raises `ValueError("project_root must be an existing directory")`;
- derives the shared rate directory only as `<resolved_project_root>/workspace/sec/rate`;
- creates missing `workspace/sec/rate` components only beneath the resolved canonical root, then resolves the resulting rate directory and requires it to remain inside that root;
- rejects a rate-directory path component that is a symlink/junction/reparse-point escape and rejects existing lock/state/temp paths that are symlinks, directories or non-regular files;
- any containment/type/safe-create failure => `P11_RATE_LIMIT_SCOPE_UNSAFE` before network access;
- never derives project root from cwd, `__file__`, a Git worktree path, a temporary directory, or the process executable;
- never silently substitutes the current worktree as project root.

Main/worktree executions participating in one supported FFDF installation MUST be wired by orchestration to the same canonical root. Passing different roots intentionally defines different unsupported installations and cannot be assumed rate-coordinated. P11-D implementation tests must prove that changing cwd/worktree does not change the gate path when the same explicit canonical root is passed.

## 5. User-Agent configuration

Exact configuration source:

`SEC_USER_AGENT`

It is read from the process environment exactly once during `SecHttpClient` construction.

No fallback is permitted from:

- OS username;
- Git name/email;
- package metadata;
- hostname;
- fabricated project contact;
- default Python/urllib identity.

Missing or invalid configuration => `SecHttpError.reason_code = "P11_USER_AGENT_REQUIRED"` before any network request.

Exact accepted grammar:

- ASCII only;
- byte length 8 through 256 inclusive;
- every byte in visible ASCII range `0x20..0x7e`;
- no leading/trailing ASCII whitespace;
- at least two ASCII-whitespace-separated tokens;
- at least one token contains exactly one `@` with non-empty text on both sides;
- CR/LF/TAB and every control character are rejected.

The value is sent exactly as configured after validation; it is not rewritten.

The raw value MUST NOT be persisted in source-package identity, parsed artifacts or deterministic IDs. Normal runtime diagnostics may record only:

- `user_agent_configured=true`;
- SHA256 of the exact ASCII User-Agent bytes.

The contact identity itself is not logged by the P11 HTTP client.

## 6. Request headers / method

P11-D discovery uses HTTP `GET` only.

Exact application request headers for JSON discovery:

```text
User-Agent: <validated SEC_USER_AGENT>
Accept: application/json
Accept-Encoding: identity
```

HTTP/1.1 `Host` is generated only from the already validated target authority; default port 443 is not appended. No caller can override `Host`. P11-D generates no Cookie, Authorization, Referer, Range or conditional-cache header. A fresh connection is closed after the attempt/response and is not pooled across requests.

`Accept-Encoding: identity` is normative so body-size accounting and preserved response bytes refer to the same entity bytes consumed by JSON parsing.

### 6.1 TLS / proxy boundary

P11-D connects directly with standard-library HTTPS and does not consume HTTP(S) proxy environment variables. TLS uses `ssl.create_default_context()` semantics with certificate verification required and hostname checking enabled. P11-D exposes no caller option to disable certificate/hostname verification or provide an unverified SSL context.

TLS certificate/hostname failure is non-retryable `P11_HTTP_FAILED`. Any connection prepared before rate-gate acquisition MUST be closed if later rate-gate acquisition/validation fails.

## 7. URL / host / scheme rules

Allowed schemes:

- `https` only.

Allowed exact ASCII lowercase hosts:

- `data.sec.gov`
- `www.sec.gov`
- `sec.gov`

Rules:

- hostname comparison is case-insensitive after ASCII lowercase normalization;
- trailing-dot hostnames are rejected;
- userinfo is rejected;
- explicit port is permitted only when equal to `443`;
- fragments are rejected;
- `file:`, `http:`, UNC/local paths and every non-HTTPS scheme are rejected before network access;
- arbitrary caller hostnames are rejected;
- taxonomy hosts are outside P11-D.

Initial URL violation => `P11_SOURCE_HOST_NOT_ALLOWED`.

### 7.1 Content-class endpoint grammar

The initial requested URL MUST also match its `SecContentClass` exactly:

- `TICKER_MAPPING_JSON`: scheme `https`, host exactly `www.sec.gov`, path exactly `/files/company_tickers.json`, empty query;
- `SUBMISSIONS_CURRENT_JSON`: scheme `https`, host exactly `data.sec.gov`, path matching `^/submissions/CIK[0-9]{10}\.json$`, empty query;
- `SUBMISSIONS_HISTORY_JSON`: scheme `https`, host exactly `data.sec.gov`, path exactly `/submissions/<validated-shard-basename>`, empty query.

Percent-encoded path alternatives are not canonical and are rejected. `get_json()` is therefore not an arbitrary allowlisted-host fetch primitive.

For redirects, the host may change only within the Section 7 allowlist, but the normalized path MUST remain valid for the same content class and query MUST remain empty. A redirect cannot change the logical endpoint/content class. Path/query/content-class violation on redirect => `P11_REDIRECT_NOT_ALLOWED`.

## 8. Timeouts and logical deadline

Exact values:

- DNS/TCP/TLS connection-preparation timeout = 10.0 seconds for the HTTPS connection attempt;
- HTTP request-header send socket timeout while the shared gate is held = 10.0 seconds;
- response/read-idle socket timeout = 30.0 seconds;
- logical fetch wall-clock deadline = 120.0 seconds from `get_json()` entry.

The logical deadline includes:

- rate-gate wait;
- retry backoff;
- Retry-After wait;
- redirects;
- network I/O.

No request/retry may begin if it cannot stay inside the remaining logical deadline.

Deadline/transport exhaustion => `P11_HTTP_FAILED`, except an unfulfilled 429 Retry-After requirement maps to `P11_RATE_LIMITED`.

## 9. Response-size limits

Exact entity-body byte caps:

| `SecContentClass` | Maximum bytes |
|---|---:|
| `TICKER_MAPPING_JSON` | 16 MiB = 16,777,216 |
| `SUBMISSIONS_CURRENT_JSON` | 32 MiB = 33,554,432 |
| `SUBMISSIONS_HISTORY_JSON` | 16 MiB = 16,777,216 |

Response framing/header cardinality is validated before body read. Header names are matched case-insensitively and **all field instances** are inspected; implementations MUST NOT collapse repeated framing fields before validation.

Exact framing rules:

1. `Transfer-Encoding` may be absent or present as exactly **one** header field. More than one Transfer-Encoding field => `P11_HTTP_FAILED`.
2. when present, its value after ASCII SP/HTAB trim and ASCII lowercase MUST be exactly `chunked`; comma lists, parameters, empty value and every other coding => `P11_HTTP_FAILED`.
3. `Content-Length` may be absent or present as exactly **one** header field; more than one is rejected even when values are textually equal.
4. Transfer-Encoding and Content-Length MUST NOT coexist; any response containing both => `P11_HTTP_FAILED` before body read.
5. when Transfer-Encoding is absent and Content-Length is present, its trimmed value MUST match `^[0-9]+$`; if greater than the class cap, abort before body read.
6. when Transfer-Encoding is exactly `chunked`, the standard-library framing layer dechunks the response and P11 counts/caps the **dechunked entity bytes** delivered by that layer. Chunk framing/trailers never enter `SecHttpResponse.body`; Content-Length parity is not evaluated because Content-Length is forbidden with chunked.
7. regardless of framing, stream/count exact delivered entity bytes and abort with `P11_RESPONSE_TOO_LARGE` as soon as the cap is exceeded.
8. for non-chunked responses with a valid Content-Length, actual EOF entity-byte count MUST equal the declared length; mismatch => `P11_HTTP_FAILED`.
9. never parse a truncated or framing-invalid body.

Exceeded cap => `P11_RESPONSE_TOO_LARGE`.

These caps do not authorize P11-E filing/package asset sizes.

## 10. HTTP success / content type / JSON encoding

Response classification order is normative:

1. handle allowed redirect statuses under Section 11 before JSON validation;
2. handle 429 under Sections 12-13;
3. handle retryable 5xx under Section 12;
4. every other non-200 status fails without JSON content-type/body parsing;
5. only status 200 proceeds to Content-Length / Content-Type / Content-Encoding / body / UTF-8 / JSON validation.

Only HTTP status `200` is a successful JSON fetch.

Successful JSON responses require exactly **one** `Content-Type` header field. After ASCII SP/HTAB trim and ASCII lowercase, its entire value MUST be exactly `application/json`. Parameters are not accepted in P11-D v1. Missing, repeated or different Content-Type => `P11_CONTENT_TYPE_INVALID`. A future SEC content-type change requires a reviewed Design-First amendment rather than ad hoc parser widening.

`Content-Encoding` may be absent or present as exactly **one** header field. When present, after ASCII SP/HTAB trim and ASCII lowercase its entire value MUST be exactly `identity`. Repeated fields, comma lists and every other content-coding => `P11_HTTP_FAILED`; P11-D never transparently decompresses discovery JSON.

JSON body rules:

- exact body bytes are preserved in `SecHttpResponse.body`;
- JSON decoding is strict UTF-8;
- UTF-8 BOM is rejected;
- invalid UTF-8 or malformed JSON => `P11_HTTP_FAILED` at HTTP-client JSON boundary;
- structurally valid JSON with invalid/missing SEC discovery fields => `P11_SUBMISSIONS_INVALID` in discovery layer.

## 11. Redirect contract

Automatic library redirect handling MUST be disabled.

Recognized redirect statuses:

- 301
- 302
- 303
- 307
- 308

Exact redirect maximum:

- at most 3 followed redirect hops per logical fetch.

Every redirect:

- requires exactly one `Location` header field with a non-empty value; missing or repeated Location => `P11_REDIRECT_NOT_ALLOWED`;
- resolves relative Location against the current URL;
- revalidates scheme/host/port/userinfo/fragment under Section 7;
- obtains a new shared rate-gate reservation;
- increments both redirect and outbound-start accounting.

Invalid redirect, loop, disallowed target, missing Location or redirect count >3 => `P11_REDIRECT_NOT_ALLOWED`.

Redirects do not reset retry counters or the 120-second logical deadline. A followed redirect increments `redirect_count` exactly once; it does not increment `retry_count`.

## 12. Retry contract

Counter semantics are logical-fetch-global:

- `retry_count` starts at 0 and increments exactly once only when a retryable failure causes another attempt to be scheduled; redirects do not increment it;
- at most 3 retries may be scheduled, so `retry_count` is 0..3;
- `redirect_count` starts at 0 and increments only when a validated redirect is followed; it is 0..3;
- neither counter resets after redirects or retries.

Exact retry maximum:

- at most 3 retries after the initial attempt.

Deterministic fallback backoff before retry 1/2/3:

- 1 second;
- 2 seconds;
- 4 seconds.

No jitter in P11 v1.

A logical fetch has an additional absolute cap of 8 emitted/potentially-emitted outbound request starts total, including initial attempts, retries and redirect hops. `outbound_start_count` starts at 0 and increments at Section 14.3 step 7 immediately before header emission, therefore including partial-send failures. Connection-preparation failures before that step do not increment it.

Before any new send transition, if `outbound_start_count == 8`, no ninth send occurs. Mapping:

- if the pending action is a retry after HTTP 429 => `P11_RATE_LIMITED`;
- if the pending action is any other retry => `P11_HTTP_FAILED`;
- if the pending action is following an otherwise valid redirect => `P11_HTTP_FAILED` with outbound-start-cap diagnostic context;
- a successful HTTP 200 received from the eighth emitted start succeeds normally.

Retryable:

- HTTP 429;
- HTTP 500..599;
- connect timeout;
- read timeout;
- connection reset/aborted transport failure.

Non-retryable:

- 400..499 except 429;
- DNS resolution failure;
- TLS certificate/hostname validation failure;
- malformed redirect;
- host/scheme rejection;
- response-size violation;
- content-type violation;
- malformed/invalid UTF-8 JSON.

403/access denied is never retried and surfaces `P11_HTTP_FAILED` with blocked/access-denied diagnostic context.

404 is never retried and surfaces `P11_HTTP_FAILED`; discovery may subsequently map absence of a required official resource to its higher-level deterministic reason code.

Exhausted 5xx/transport retry => `P11_HTTP_FAILED`.

## 13. Retry-After

For HTTP 429 only, `Retry-After` may be absent or appear as exactly one header field. More than one Retry-After field is ambiguous and returns `P11_RATE_LIMITED` without retry.

When one Retry-After field is present, recognized forms are:

- non-negative ASCII decimal integer seconds (`^[0-9]+$`);
- IMF-fixdate only, exact English/GMT grammar `ddd, DD Mon YYYY HH:MM:SS GMT`; obsolete RFC850/asctime date forms are not accepted.

For a valid value, required wait is:

`max(fallback_backoff_for_this_retry, Retry-After remaining duration)`

For IMF-fixdate, remaining duration is computed against current UTC wall time and MUST NOT be rounded down; the implementation waits until the represented instant has passed. Subsequent waiting/deadline enforcement uses monotonic time so wall-clock adjustment cannot shorten the already computed wait.

Exact maximum acceptable Retry-After wait = 60 seconds.

If the required Retry-After wait is >60 seconds, or cannot fit inside the remaining 120-second logical deadline:

- do not retry early;
- return `P11_RATE_LIMITED`.

Malformed Retry-After falls back to the deterministic 1/2/4-second schedule.

## 14. Cross-process rate gate

Canonical directory:

`<project_root>/workspace/sec/rate/`

Exact files:

- lock: `sec-rate-gate.lock`
- state: `sec-rate-gate-v1.json`

Windows v1 lock primitive:

- open/create lock file inside canonical directory;
- ensure byte 0 exists;
- exclusive non-blocking byte-range lock using `msvcrt.locking(..., LK_NBLCK, 1)`;
- poll every 25 ms;
- maximum lock-acquisition duration = 5.0 seconds.

Failure to acquire a safe shared lock within 5.0 seconds => `P11_RATE_LIMIT_SCOPE_UNSAFE` and no outbound request.

The lock file is never deleted/recreated to break a live lock.

### 14.1 State schema

Exact canonical state object:

```json
{
  "last_start_monotonic_ns": 0,
  "last_start_unix_ns": 0,
  "phase": "READY",
  "schema_version": "p11-sec-rate-gate-v1"
}
```

Rules:

- exact keys only;
- `phase` is exactly `READY` or `RESERVED`;
- integer timestamps >=0;
- `schema_version` exact;
- canonical JSON = UTF-8, sorted keys, compact separators, one trailing LF;
- state file is runtime coordination only and never enters source/package/parsed identity.
- each state update is written to sibling `sec-rate-gate-v1.json.tmp` while the exclusive byte lock is held, flushed and `os.fsync()`ed, then committed with same-directory `os.replace()`; a stale `.tmp` may be truncated/reused only while the exclusive lock is held.

### 14.2 Connection and request-start boundary

P11-D uses a fresh HTTPS connection for each outbound HTTP attempt/hop; connection pooling is outside v1.

DNS/TCP/TLS connection preparation may occur before rate-gate acquisition, but **no HTTP request bytes may be sent before the shared gate is held and the request-start transition below is complete**. A connection-preparation failure consumes the retry budget/backoff policy but does not increment `outbound_start_count`, because no HTTP request was emitted. Every retry/hop that actually emits HTTP request bytes must pass through this same gate.

The implementation must use a transport boundary that separates connection establishment from HTTP header emission (for example standard-library `http.client.HTTPSConnection.connect()` followed later by explicit request/header send). Automatic `urllib` request dispatch that can send headers before the rate-gate transition is not permitted.

### 14.3 Request-start transition

While holding the exclusive byte lock:

1. read state if present;
2. if state is missing, malformed, has unexpected keys/version/types, has `phase=RESERVED`, or the persisted monotonic value cannot be safely compared, use conservative recovery: wait a full 125 ms while still holding the kernel lock;
3. otherwise (`phase=READY`) compare current `time.monotonic_ns()` with `last_start_monotonic_ns`;
4. if elapsed <125,000,000 ns, wait the remaining duration while holding the lock;
5. after the wait, sample fresh monotonic/Unix times and atomically write `phase=RESERVED` with those timestamps; this write is a crash marker, not yet the accepted start timestamp;
6. if the RESERVED write/replace fails, release and return `P11_RATE_LIMIT_SCOPE_UNSAFE`; no HTTP request bytes may be sent;
7. while still holding the same kernel lock, increment the logical fetch `outbound_start_count` exactly once for this send transition, then emit the HTTP request line + headers on the already prepared TLS connection; entering this step counts even if header emission later raises because partial HTTP bytes may already have left the process;
8. whether header emission succeeds or raises after any possible partial send, sample fresh monotonic/Unix times and atomically write `phase=READY` with that **post-send safe timestamp** before normal lock release;
9. if the READY write fails, close the connection, release the kernel lock, return `P11_RATE_LIMIT_SCOPE_UNSAFE`, and treat the attempt as potentially emitted; a later process that observes the retained RESERVED state takes the full conservative recovery wait;
10. release the lock only after the READY state is durably replaced;
11. only then wait for/read the HTTP response.

The post-send READY timestamp is deliberately conservative: the next outbound HTTP start is delayed at least 125 ms after request-header emission has returned, so scheduler delay between reservation and send cannot collapse real request-start spacing.

If persisted `last_start_monotonic_ns` is greater than current monotonic time (for example after reboot), it is non-comparable and uses the full 125 ms recovery path. A retained `RESERVED` phase always uses the full 125 ms recovery path regardless of timestamp.

### 14.4 Crash / stale recovery

The kernel byte-range lock is process-owned and is released by Windows when the holder exits/crashes.

No PID/mtime heuristic may break a lock held by another live process.

Crash safety:

- crash before RESERVED commit => no HTTP request permission was granted;
- crash after RESERVED commit but before/during send => next holder sees RESERVED and waits a full 125 ms before another send;
- crash after send but before READY commit => next holder still sees RESERVED and waits a full 125 ms;
- crash after READY commit => next holder waits from the post-send READY timestamp.

If state is missing/corrupted but the kernel lock can be acquired safely, the next holder waits a full 125 ms before beginning a new RESERVED transition. If the kernel lock itself cannot be safely acquired, block with `P11_RATE_LIMIT_SCOPE_UNSAFE`.

## 15. Discovery endpoint construction

Ticker mapping URL is fixed:

`https://www.sec.gov/files/company_tickers.json`

Current Submissions URL is constructed only as:

`https://data.sec.gov/submissions/CIK##########.json`

where CIK is the accepted normalized 10-digit CIK.

Historical shard URL is constructed only as:

`https://data.sec.gov/submissions/<validated-shard-basename>`

Historical shard basename:

- comes only from current Submissions `filings.files[].name`;
- non-empty visible ASCII basename;
- no slash/backslash/control/query/fragment;
- suffix `.json` case-sensitive;
- never caller supplied as a path/URL.

No arbitrary URL is accepted by discovery APIs.

## 16. Discovery JSON normalization

Discovery input validation before network:

- `cik` must pass accepted P11-C normalization;
- `target_base_forms` must be a non-empty tuple; every element must pass P11-C SEC-form normalization and filtering uses its `base_form` (an `/A` input therefore denotes the same form family, not an amendment-selection policy);
- normalized target base forms are deduped and ASCII-sorted;
- `filing_date_from` and `filing_date_to` are exact valid `YYYY-MM-DD`, with `from <= to`;
- `target_accession`, when non-null, must pass P11-C accession normalization;
- invalid caller arguments raise `ValueError` before any network request and do not masquerade as provider-data reason codes.

### 16.1 Ticker mapping

`load_sec_ticker_rows()`:

- response must be a JSON object whose row values are JSON objects;
- each accepted row requires keys `cik_str`, `ticker`, and `title`; extra row keys are permitted as forward-compatible SEC metadata but are ignored and never identity inputs;
- `ticker` and `title` are JSON strings; ticker normalization uses accepted P11-C ASCII trim/uppercase rules;
- `cik_str` is a JSON integer, **not** a string/float/bool; accepted numeric range is 1 through 9,999,999,999 inclusive; canonicalize with ASCII decimal `str(cik_str)` and then accepted P11-C `normalize_cik`;
- exact duplicate `(ticker, cik)` rows dedupe;
- one ticker mapping to multiple distinct CIKs is retained as multiple rows so identity resolution can return `P11_COMPANY_IDENTITY_AMBIGUOUS`;
- output canonical sort = `(ticker ASC, cik ASC)`.

Malformed top-level/row structure => `P11_SUBMISSIONS_INVALID`.

### 16.2 Current + historical Submissions

Current response exact shape:

- top level is a JSON object;
- `cik` is a JSON string accepted by P11-C `normalize_cik` and MUST normalize exactly to the requested filer CIK;
- `filings` is a JSON object;
- `filings.recent` is a JSON object containing all eight required parallel arrays listed below;
- `filings.files` is a JSON array of historical-shard descriptor objects.

Historical shard descriptor exact required fields:

- `name`: JSON string; accepted shard safe-basename grammar from Section 15;
- `filingFrom`: JSON string, exact valid `YYYY-MM-DD`;
- `filingTo`: JSON string, exact valid `YYYY-MM-DD`;
- `filingCount`: JSON integer >=0 (bool rejected).

Unexpected descriptor keys are permitted as SEC forward-compatible metadata but are ignored and never identity inputs. `filingFrom <= filingTo` is required. Invalid descriptor required fields/date interval => `P11_SUBMISSIONS_INVALID`.

Historical descriptor normalization is completed **before** overlap filtering or any shard fetch:

1. validate every raw descriptor in `filings.files`; an invalid descriptor blocks even if its declared interval would be outside the requested window;
2. normalized required descriptor tuple = `(name, filingFrom, filingTo, filingCount)`;
3. group normalized descriptors by exact case-sensitive `name`;
4. if repeated rows for one `name` have identical normalized required tuples, collapse them to one descriptor; differences only in ignored extra SEC metadata do not create a conflict;
5. if one `name` has any different required value (`filingFrom`, `filingTo`, or `filingCount`), fail closed with `P11_SUBMISSIONS_INVALID`; first-wins/last-wins is forbidden;
6. after dedupe, canonical descriptor order = `(filingFrom ASC, filingTo ASC, name ASC)` using the normalized date strings and ASCII filename;
7. apply inclusive interval overlap against the requested filing window only after this validation/dedupe/sort step;
8. fetch each selected descriptor `name` exactly once and in canonical descriptor order.

Different descriptor names may share/overlap date intervals and remain distinct. Descriptor array input order is never a fetch-order or identity input.

Historical shard response exact shape:

- top level is a JSON object;
- it contains the same eight required parallel arrays as `filings.recent`;
- no nested `filings` wrapper is expected for the shard;
- the descriptor `filingCount` MUST equal the common length of the eight required arrays in the fetched shard; mismatch => `P11_SUBMISSIONS_INVALID`.

The eight required parallel arrays for both current `filings.recent` and each fetched historical shard are exactly:

1. `accessionNumber`;
2. `filingDate`;
3. `reportDate`;
4. `form`;
5. `primaryDocument`;
6. `primaryDocDescription`;
7. `isXBRL`;
8. `isInlineXBRL`.

Rules:

- every required member MUST be a JSON array;
- all eight arrays in one source object MUST have exactly equal length;
- no `zip()`-style truncation or shortest-array behavior is permitted; any length mismatch => `P11_SUBMISSIONS_INVALID`;
- `accessionNumber`, `filingDate`, `reportDate`, `form`, `primaryDocument`, and `primaryDocDescription` elements MUST be JSON strings;
- `isXBRL` and `isInlineXBRL` elements MUST be JSON integers exactly `0` or `1`; bool/string/other integers are invalid;
- normalize 0 => `False`, 1 => `True`; P11-D candidate booleans are therefore non-null for accepted current/history rows;
- `reportDate == ""` normalizes to null; any non-empty reportDate must be exact valid `YYYY-MM-DD`;
- `primaryDocDescription == ""` normalizes to null; otherwise preserve the exact provider string;
- `filingDate` must be exact valid `YYYY-MM-DD`;
- `primaryDocument` must pass the accepted safe-basename rules before becoming a candidate;
- accession and form normalization use accepted P11-C rules.

Current rows and fetched historical rows are normalized through this same candidate validator. CIK for every candidate is the normalized requested filer CIK confirmed by the current Submissions root.

## 17. Deterministic merge / duplicate accession

Source array order, shard fetch order and discovery provenance URL order are never filing semantic identity inputs.

All normalized current + historical candidates merge by exact normalized `accession_number`.

For each normalized source row, `submission_source_urls` initially contains exactly one canonical **requested** Submissions JSON URL: the current `CIK##########.json` URL or the validated historical-shard URL. Redirect final URLs and timing/receipt URLs do not enter this tuple.

If the same accession appears more than once:

1. compare only semantic candidate fields (all dataclass fields with `compare=True`); `submission_source_urls` is excluded;
2. if any semantic field differs, fail closed with `P11_SUBMISSIONS_INVALID`;
3. if semantic fields are equal, keep one semantic row and set `submission_source_urls` to the ASCII-lexicographically sorted unique union of all contributing canonical requested source URLs;
4. duplicate provenance URLs collapse to one entry; the tuple is always non-empty;
5. current-vs-history source location, shard fetch order and duplicate source-row order therefore cannot create a false filing conflict or change semantic equality/order.

`SecDiscoveryCandidate.__eq__` and generated hash semantics follow the same rule because `submission_source_urls` is `field(compare=False)`. No `<`, `<=`, `>`, `>=` ordering contract is generated. Code MUST NOT use `dataclasses.asdict()` or full serialized-object equality as the duplicate semantic comparator unless provenance is explicitly removed first.

Canonical output sorting MUST always use the explicit key below; implementation MUST NOT rely on dataclass/native tuple comparison of optional semantic fields.

Canonical output sort:

1. `filing_date` ascending;
2. `accession_number` ascending.

Filtering:

- `target_base_forms` are normalized, deduped and sorted before matching;
- filing window is inclusive `[filing_date_from, filing_date_to]`;
- if `target_accession` is supplied, it is normalized using the accepted P11-C accession grammar and final output must contain exactly that accession or return `P11_FILING_NOT_FOUND`;
- discovery does not silently choose one amendment/original variant when multiple relevant accessions remain.

Variant policy remains design/26 Section 24: ambiguous original/amended variants without explicit caller policy => `P11_FILING_VARIANT_REVIEW_REQUIRED` at the planning/selection boundary.

## 18. Failure mapping

Exact client-layer mapping:

| Condition | reason_code |
|---|---|
| missing/invalid User-Agent | `P11_USER_AGENT_REQUIRED` |
| unsafe/unavailable shared rate coordination | `P11_RATE_LIMIT_SCOPE_UNSAFE` |
| exhausted/unacceptable 429 wait | `P11_RATE_LIMITED` |
| initial non-HTTPS/disallowed host/port/userinfo/fragment | `P11_SOURCE_HOST_NOT_ALLOWED` |
| invalid/disallowed/excess redirect | `P11_REDIRECT_NOT_ALLOWED` |
| timeout, transport failure, invalid/ambiguous HTTP framing headers, non-retried 403/404, exhausted 5xx, malformed UTF-8/JSON | `P11_HTTP_FAILED` |
| body over cap | `P11_RESPONSE_TOO_LARGE` |
| invalid/missing JSON content type | `P11_CONTENT_TYPE_INVALID` |
| valid JSON with invalid SEC discovery schema/fields/conflicting duplicate accession | `P11_SUBMISSIONS_INVALID` |
| requested filing/accession absent after deterministic merge | `P11_FILING_NOT_FOUND` |

Errors must not include raw User-Agent contact text.

## 19. Receipt / diagnostics boundary

For every successful fetch, runtime diagnostics may record:

- requested URL;
- final URL;
- status;
- normalized content type;
- byte count;
- SHA256 of exact body bytes;
- redirect count;
- outbound-start count;
- retry count;
- User-Agent SHA256 only;
- acquisition timestamp/timing diagnostics.

Timing/retry/header diagnostics do not enter source-package identity unless a later package contract explicitly includes a field. Exact response body bytes and their SHA256 remain source evidence when later package gates authorize capture.

## 20. P11-D / P11-E boundary

P11-D may fetch only the three JSON content classes defined here.

P11-D MUST NOT fetch or persist:

- filing primary HTML/XML;
- accession `index.json` for package capture;
- `.xsd` / filing taxonomy dependencies;
- exhibits;
- content-addressed raw assets.

Those actions begin only in separately authorized P11-E package acquisition/storage work.

The P11-D HTTP primitive may later be reused by P11-E only after P11-E separately freezes/accepts asset content classes and size caps. P11-D JSON caps MUST NOT be reused as implicit package-asset caps.

## 21. Mandatory design/implementation tests

Before P11-D implementation can close, focused tests must prove at least:

1. missing User-Agent blocks before network;
2. malformed/non-ASCII/control User-Agent blocks;
3. configured grammar-valid User-Agent is sent exactly and raw value is not logged;
4. same explicit canonical project root produces the same rate-gate path regardless of cwd/worktree; no cwd/module-path root autodiscovery
5. rate-directory containment rejects symlink/junction/reparse escape and non-regular lock/state/temp paths before network
6. initial http/file/bad host rejected before network;
7. content-class URL grammar rejects arbitrary allowlisted-host paths, query strings and percent-encoded alternatives;
8. explicit non-443 port rejected;
9. redirect auto-follow disabled;
10. allowed same-content-class redirect manually follows through a second request-start transition;
11. redirect to bad host/path/query blocked;
12. redirect >3 blocked;
13. missing/repeated Location header is rejected and a followed redirect increments redirect_count but not retry_count
14. 10s connect / 10s header-send / 30s read / 120s logical deadline behavior is bounded;
15. connection preparation occurs before the shared send gate and emits no HTTP request bytes;
16. TLS uses verified default context/hostname checking with no proxy or unverified-context escape hatch
17. a prepared HTTPS connection is closed when later rate-gate acquisition/validation fails
18. each JSON content class cap enforced by Content-Length and streaming count;
19. single `Transfer-Encoding: chunked` with no Content-Length is accepted and cap counts dechunked entity bytes
20. Transfer-Encoding plus Content-Length is rejected before body read
21. repeated Transfer-Encoding, repeated Content-Length, comma-list/multi-token or unsupported transfer coding is rejected
22. non-chunked single Content-Length requires exact EOF parity while chunked response never applies Content-Length parity
23. Content-Type must be exactly one field with entire normalized value `application/json`; parameters/repeats are rejected
24. Content-Encoding absent or exactly one `identity`; repeats/lists/other codings are rejected
25. partial/failed header-send transition still increments outbound_start_count exactly once while connection-preparation failure does not
26. malformed/conflicting Content-Length and declared-vs-actual mismatch fail closed;
27. wrong/missing content type blocked;
28. non-identity Content-Encoding blocked;
29. invalid UTF-8/BOM/malformed JSON blocked;
30. 403 no retry;
31. 404 no retry storm;
32. 5xx max three retries with exact 1/2/4 schedule;
33. 429 Retry-After seconds;
34. 429 Retry-After HTTP-date with no downward rounding;
35. multiple Retry-After fields fail closed as `P11_RATE_LIMITED` without retry
36. Retry-After >60s fails without early retry;
37. total emitted HTTP outbound-start cap =8;
38. eighth-start HTTP 200 succeeds; a pending ninth redirect/retry is blocked with the exact cap-exhaustion mapping
39. partial-send failure counts one outbound start but increments retry_count only if another retry is actually scheduled
40. redirect/retry interleaving preserves global retry_count 0..3 and redirect_count 0..3 without reset
41. every retry/redirect that emits request bytes passes through shared gate;
42. two-process shared-root gate observes >=125ms between actual simulated HTTP header-send starts and <=8 starts in every half-open one-second window;
43. crash-holder OS lock release recovery;
44. malformed/missing/RESERVED state takes full 125ms conservative recovery before reset;
45. a simulated sender delayed after reservation cannot collapse actual send spacing because the kernel lock is held through header emission and READY records a post-send safe timestamp;
46. lock acquisition >5s blocks with `P11_RATE_LIMIT_SCOPE_UNSAFE`;
47. connection-preparation failure consumes retry budget but not emitted-request count;
48. current-only discovery;
49. historical-shard discovery;
50. non-overlapping historical shard not fetched;
51. required parallel arrays must all exist and have equal lengths;
52. `isXBRL`/`isInlineXBRL` accept integer 0/1 only;
53. public `SecDiscoveryCandidate.is_xbrl` and `is_inline_xbrl` are non-null bool for every accepted row
54. `SecDiscoveryCandidate` exposes no generated rich ordering; canonical sort with mixed null/non-null optional fields uses only `(filing_date, accession_number)` and cannot raise cross-type comparison errors
55. historical descriptor `filingCount` must equal shard row count;
56. exact duplicate historical descriptors with the same required tuple collapse and fetch one shard even when ignored extra metadata differs
57. same historical descriptor name with different filingFrom/filingTo/filingCount => `P11_SUBMISSIONS_INVALID` before overlap filtering
58. historical descriptor input reorder yields identical canonical `(filingFrom, filingTo, name)` selected fetch order
59. ticker `cik_str` accepts JSON integer only (bool/string/float rejected) and normalizes to 10-digit CIK;
60. duplicate identical accession dedupes;
61. same-accession semantic-equal current/history rows with different source URLs dedupe and produce one ASCII-sorted unique provenance tuple
62. provenance tuple content/order is excluded from candidate equality/hash and cannot create a semantic conflict
63. duplicate conflicting accession => `P11_SUBMISSIONS_INVALID`;
64. current/shard input order changes do not change canonical output;
65. ticker rows sorted `(ticker,cik)` and ambiguity retained;
66. target accession exact match / not-found behavior;
67. no silent amendment supersession;
68. no P11-E package/asset write or fetch occurs.

## 22. Implementation authorization gate

This contract is not implementation authorization.

Required sequence:

1. freeze this amended design;
2. create evidence showing contract completeness and environment compatibility;
3. fresh detached design review;
4. only PASS may authorize P11-D production/test implementation separately.

Until then:

- P11-D implementation = CLOSED;
- P11 provider production = CLOSED.
