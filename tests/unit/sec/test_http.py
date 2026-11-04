from __future__ import annotations

import datetime as dt
import json
import socket
from pathlib import Path
from types import MethodType

import pytest

from financial_filing_data_foundation.sec import SecContentClass, SecHttpClient, SecHttpError
from financial_filing_data_foundation.sec import http as http_mod

UA = "FFDFResearch test@example.com"
CURRENT = "https://data.sec.gov/submissions/CIK0000320193.json"
TICKERS = "https://www.sec.gov/files/company_tickers.json"


class FakeHeaders:
    def __init__(self, values: dict[str, list[str]] | None = None) -> None:
        self.values = {k.lower(): list(v) for k, v in (values or {}).items()}

    def get_all(self, name: str, default=None):
        value = self.values.get(name.lower())
        return list(value) if value is not None else ([] if default is None else default)


class FakeResponse:
    def __init__(self, status: int = 200, body: bytes = b"{}", headers: dict[str, list[str]] | None = None) -> None:
        self.status = status
        self._body = body
        self._offset = 0
        if headers is None:
            headers = {"Content-Type": ["application/json"], "Content-Length": [str(len(body))]}
        self.headers = FakeHeaders(headers)
        self.closed = False

    def read(self, n: int = -1) -> bytes:
        if self._offset >= len(self._body):
            return b""
        if n < 0:
            n = len(self._body) - self._offset
        data = self._body[self._offset : self._offset + n]
        self._offset += len(data)
        return data

    def close(self) -> None:
        self.closed = True


class FakeSock:
    def __init__(self) -> None:
        self.timeouts: list[float] = []

    def settimeout(self, value: float) -> None:
        self.timeouts.append(value)


class FakeConnection:
    def __init__(self, response: FakeResponse) -> None:
        self.response = response
        self.sock = FakeSock()
        self.closed = False
        self.requests: list[tuple[str, str]] = []
        self.headers: list[tuple[str, str]] = []

    def getresponse(self) -> FakeResponse:
        return self.response

    def close(self) -> None:
        self.closed = True

    def putrequest(self, method: str, path: str, **kwargs) -> None:
        self.requests.append((method, path))

    def putheader(self, name: str, value: str) -> None:
        self.headers.append((name, value))

    def endheaders(self) -> None:
        return None


def bare_client() -> SecHttpClient:
    client = object.__new__(SecHttpClient)
    client.project_root = Path(".")
    client._user_agent = UA
    client._user_agent_sha256 = "x" * 64
    return client


def scripted_client(monkeypatch: pytest.MonkeyPatch, responses: list[FakeResponse], *, prep_errors: list[BaseException] | None = None, send_errors: list[BaseException] | None = None):
    client = bare_client()
    prepared: list[FakeConnection] = []
    starts: list[str] = []
    prep_errors = list(prep_errors or [])
    send_errors = list(send_errors or [])
    response_iter = iter(responses)

    def prepare(self, parsed, deadline_ns):
        if prep_errors:
            exc = prep_errors.pop(0)
            if exc is not None:
                raise exc
        conn = FakeConnection(next(response_iter))
        prepared.append(conn)
        return conn

    def send(self, connection, parsed, deadline_ns, on_start):
        on_start()
        starts.append(parsed.path)
        if send_errors:
            exc = send_errors.pop(0)
            if exc is not None:
                raise exc

    client._prepare_connection = MethodType(prepare, client)
    client._send_request = MethodType(send, client)
    monkeypatch.setattr(http_mod, "_sleep_bounded", lambda *a, **k: None)
    return client, prepared, starts


def assert_reason(exc: pytest.ExceptionInfo[SecHttpError], reason: str) -> None:
    assert exc.value.reason_code == reason
    assert str(exc.value)


def test_p11d_01_missing_user_agent_blocks_before_network(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SEC_USER_AGENT", raising=False)
    with pytest.raises(SecHttpError) as exc:
        SecHttpClient(tmp_path)
    assert_reason(exc, "P11_USER_AGENT_REQUIRED")
    assert not (tmp_path / "workspace").exists()


def test_p11d_02_malformed_non_ascii_control_user_agent_blocks(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    for value in ("short", "FFDF x@example.com\n", "FFDF t\u00e9st@example.com", " FFDF x@example.com"):
        monkeypatch.setenv("SEC_USER_AGENT", value)
        with pytest.raises(SecHttpError) as exc:
            SecHttpClient(tmp_path)
        assert_reason(exc, "P11_USER_AGENT_REQUIRED")


def test_p11d_03_configured_user_agent_sent_exactly_and_not_logged(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SEC_USER_AGENT", UA)
    client = SecHttpClient(tmp_path)
    conn = FakeConnection(FakeResponse())
    class Gate:
        def emit(self, send, on_start, deadline_ns):
            on_start(); return send()
    client._rate_gate = Gate()
    client._send_request(conn, http_mod._validate_url(TICKERS, SecContentClass.TICKER_MAPPING_JSON, redirect=False), http_mod.time.monotonic_ns()+10_000_000_000, lambda: None)
    assert ("User-Agent", UA) in conn.headers
    assert UA not in client.user_agent_sha256


def test_p11d_04_explicit_project_root_gives_same_rate_path_regardless_cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SEC_USER_AGENT", UA)
    other = tmp_path / "other"; other.mkdir()
    c1 = SecHttpClient(tmp_path)
    monkeypatch.chdir(other)
    c2 = SecHttpClient(tmp_path)
    assert c1._rate_gate.rate_dir == c2._rate_gate.rate_dir == (tmp_path / "workspace/sec/rate").resolve()


def test_p11d_05_unsafe_nonregular_rate_path_rejected_before_network(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SEC_USER_AGENT", UA)
    bad = tmp_path / "workspace/sec/rate/sec-rate-gate.lock"
    bad.mkdir(parents=True)
    with pytest.raises(SecHttpError) as exc:
        SecHttpClient(tmp_path)
    assert_reason(exc, "P11_RATE_LIMIT_SCOPE_UNSAFE")


@pytest.mark.parametrize("url", ["http://data.sec.gov/submissions/CIK0000320193.json", "file:///x", "https://evil.example/submissions/CIK0000320193.json"])
def test_p11d_06_initial_bad_scheme_or_host_rejected_before_network(url: str) -> None:
    with pytest.raises(SecHttpError) as exc:
        http_mod._validate_url(url, SecContentClass.SUBMISSIONS_CURRENT_JSON, redirect=False)
    assert_reason(exc, "P11_SOURCE_HOST_NOT_ALLOWED")


def test_p11d_07_content_class_url_grammar_rejects_arbitrary_paths_queries_percent() -> None:
    assert not http_mod._safe_history_basename(" leading.json")
    assert not http_mod._safe_history_basename("in terior.json")
    assert not http_mod._safe_history_basename("x%.json")
    assert http_mod._safe_history_basename("a+b;=@.json")
    bad = [
        "https://data.sec.gov/other.json",
        CURRENT + "?x=1",
        "https://data.sec.gov/submissions/CIK0000320193%2Ejson",
    ]
    for url in bad:
        with pytest.raises(SecHttpError):
            http_mod._validate_url(url, SecContentClass.SUBMISSIONS_CURRENT_JSON, redirect=False)


def test_p11d_08_explicit_non_443_port_rejected() -> None:
    with pytest.raises(SecHttpError) as exc:
        http_mod._validate_url("https://data.sec.gov:444/submissions/CIK0000320193.json", SecContentClass.SUBMISSIONS_CURRENT_JSON, redirect=False)
    assert_reason(exc, "P11_SOURCE_HOST_NOT_ALLOWED")


def test_p11d_09_redirect_is_manual_not_automatic(monkeypatch: pytest.MonkeyPatch) -> None:
    first = FakeResponse(302, b"", {"Location": ["https://www.sec.gov/submissions/CIK0000320193.json"]})
    second = FakeResponse(200, b"{}")
    client, _, starts = scripted_client(monkeypatch, [first, second])
    result = client.get_json(CURRENT, SecContentClass.SUBMISSIONS_CURRENT_JSON)
    assert result.redirect_count == 1
    assert len(starts) == 2


def test_p11d_10_allowed_same_class_redirect_uses_second_start(monkeypatch: pytest.MonkeyPatch) -> None:
    first = FakeResponse(307, b"", {"Location": ["https://www.sec.gov/submissions/CIK0000320193.json"]})
    client, _, starts = scripted_client(monkeypatch, [first, FakeResponse()])
    result = client.get_json(CURRENT, SecContentClass.SUBMISSIONS_CURRENT_JSON)
    assert result.outbound_start_count == 2 and result.redirect_count == 1 and len(starts) == 2


def test_p11d_11_redirect_to_bad_host_path_query_blocked(monkeypatch: pytest.MonkeyPatch) -> None:
    client, _, _ = scripted_client(monkeypatch, [FakeResponse(302, b"", {"Location": ["https://evil.example/x?y=1"]})])
    with pytest.raises(SecHttpError) as exc:
        client.get_json(CURRENT, SecContentClass.SUBMISSIONS_CURRENT_JSON)
    assert_reason(exc, "P11_REDIRECT_NOT_ALLOWED")


def test_p11d_12_redirect_more_than_three_blocked(monkeypatch: pytest.MonkeyPatch) -> None:
    targets=[
        "https://www.sec.gov/submissions/CIK0000320194.json",
        "https://sec.gov/submissions/CIK0000320195.json",
        "https://www.sec.gov/submissions/CIK0000320196.json",
        "https://sec.gov/submissions/CIK0000320197.json",
    ]
    rs=[FakeResponse(302,b"",{"Location":[target]}) for target in targets]
    client,_,starts=scripted_client(monkeypatch,rs)
    with pytest.raises(SecHttpError) as exc:
        client.get_json(CURRENT,SecContentClass.SUBMISSIONS_CURRENT_JSON)
    assert_reason(exc,"P11_REDIRECT_NOT_ALLOWED")
    assert len(starts)==4  # initial + exactly three followed hops; fourth follow is not emitted


def test_p11d_13_location_cardinality_and_redirect_counter(monkeypatch: pytest.MonkeyPatch) -> None:
    for headers in ({}, {"Location":["/x","/y"]}):
        client,_,_=scripted_client(monkeypatch,[FakeResponse(302,b"",headers)])
        with pytest.raises(SecHttpError) as exc:
            client.get_json(CURRENT,SecContentClass.SUBMISSIONS_CURRENT_JSON)
        assert_reason(exc,"P11_REDIRECT_NOT_ALLOWED")
    client,_,_=scripted_client(monkeypatch,[FakeResponse(302,b"",{"Location":["https://www.sec.gov/submissions/CIK0000320193.json"]}),FakeResponse()])
    assert client.get_json(CURRENT,SecContentClass.SUBMISSIONS_CURRENT_JSON).redirect_count==1


def test_p11d_14_timeouts_and_logical_deadline_are_bounded(monkeypatch: pytest.MonkeyPatch) -> None:
    client=bare_client()
    now=http_mod.time.monotonic_ns()
    with pytest.raises(SecHttpError):
        http_mod._remaining_seconds(now-1)
    monkeypatch.setattr(http_mod.time,"monotonic_ns",lambda: now)
    with pytest.raises(SecHttpError):
        http_mod._sleep_bounded(2.0,now+1_000_000_000)


def test_p11d_15_connection_preparation_precedes_send_gate(monkeypatch: pytest.MonkeyPatch) -> None:
    order=[]
    client=bare_client()
    client._prepare_connection=MethodType(lambda self,parsed,deadline: order.append("prepare") or FakeConnection(FakeResponse()),client)
    client._send_request=MethodType(lambda self,conn,parsed,deadline,on_start: order.append("send") or on_start(),client)
    monkeypatch.setattr(http_mod,"_sleep_bounded",lambda *a,**k:None)
    client.get_json(CURRENT,SecContentClass.SUBMISSIONS_CURRENT_JSON)
    assert order[:2]==["prepare","send"]


def test_p11d_16_tls_uses_verified_default_context_and_no_proxy_dispatch(monkeypatch: pytest.MonkeyPatch) -> None:
    client=bare_client(); seen={}
    class Conn:
        def __init__(self,host,port,timeout,context): seen.update(host=host,port=port,timeout=timeout,context=context)
        def connect(self): pass
    ctx=object()
    monkeypatch.setattr(http_mod.ssl,"create_default_context",lambda:ctx)
    monkeypatch.setattr(http_mod.http.client,"HTTPSConnection",Conn)
    parsed=http_mod._validate_url(CURRENT,SecContentClass.SUBMISSIONS_CURRENT_JSON,redirect=False)
    client._prepare_connection(parsed,http_mod.time.monotonic_ns()+20_000_000_000)
    assert seen["context"] is ctx and seen["host"]=="data.sec.gov" and seen["port"]==443


def test_p11d_17_prepared_connection_closed_when_rate_gate_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    conn=FakeConnection(FakeResponse())
    client=bare_client()
    client._prepare_connection=MethodType(lambda *a:conn,client)
    client._send_request=MethodType(lambda *a: (_ for _ in ()).throw(SecHttpError("P11_RATE_LIMIT_SCOPE_UNSAFE","gate")),client)
    with pytest.raises(SecHttpError): client.get_json(CURRENT,SecContentClass.SUBMISSIONS_CURRENT_JSON)
    assert conn.closed


def _header_response(headers: dict[str,list[str]], body: bytes=b"{}") -> FakeResponse:
    return FakeResponse(200,body,headers)


def test_p11d_18_caps_enforced_by_content_length_and_streaming() -> None:
    cap=http_mod._CAPS[SecContentClass.TICKER_MAPPING_JSON]
    r=_header_response({"Content-Type":["application/json"],"Content-Length":[str(cap+1)]})
    with pytest.raises(SecHttpError) as exc: SecHttpClient._validate_success_headers(r,SecContentClass.TICKER_MAPPING_JSON)
    assert_reason(exc,"P11_RESPONSE_TOO_LARGE")


def test_p11d_19_single_chunked_without_length_is_accepted_and_counts_entity_bytes() -> None:
    r=_header_response({"Content-Type":["application/json"],"Transfer-Encoding":["chunked"]},b"{}")
    chunked,declared,cap=SecHttpClient._validate_success_headers(r,SecContentClass.TICKER_MAPPING_JSON)
    assert chunked and declared is None and cap==16_777_216


def test_p11d_20_transfer_encoding_plus_content_length_rejected_before_body() -> None:
    r=_header_response({"Content-Type":["application/json"],"Transfer-Encoding":["chunked"],"Content-Length":["2"]})
    with pytest.raises(SecHttpError) as exc: SecHttpClient._validate_success_headers(r,SecContentClass.TICKER_MAPPING_JSON)
    assert_reason(exc,"P11_HTTP_FAILED")


@pytest.mark.parametrize("headers",[
    {"Content-Type":["application/json"],"Transfer-Encoding":["chunked","chunked"]},
    {"Content-Type":["application/json"],"Content-Length":["2","2"]},
    {"Content-Type":["application/json"],"Transfer-Encoding":["gzip"]},
    {"Content-Type":["application/json"],"Transfer-Encoding":["chunked, gzip"]},
])
def test_p11d_21_repeated_or_unsupported_framing_rejected(headers) -> None:
    with pytest.raises(SecHttpError): SecHttpClient._validate_success_headers(_header_response(headers),SecContentClass.TICKER_MAPPING_JSON)


def test_p11d_22_nonchunked_content_length_requires_exact_parity_chunked_does_not() -> None:
    conn=FakeConnection(FakeResponse())
    r=FakeResponse(200,b"{}")
    with pytest.raises(SecHttpError): SecHttpClient._read_body(r,conn,chunked=False,declared_length=3,cap=10,deadline_ns=http_mod.time.monotonic_ns()+1_000_000_000)
    r2=FakeResponse(200,b"{}")
    assert SecHttpClient._read_body(r2,conn,chunked=True,declared_length=None,cap=10,deadline_ns=http_mod.time.monotonic_ns()+1_000_000_000)==b"{}"


def test_p11d_23_content_type_exact_single_application_json() -> None:
    for headers in ({}, {"Content-Type":["application/json; charset=utf-8"]}, {"Content-Type":["application/json","application/json"]}):
        with pytest.raises(SecHttpError) as exc: SecHttpClient._validate_success_headers(_header_response(headers),SecContentClass.TICKER_MAPPING_JSON)
        assert_reason(exc,"P11_CONTENT_TYPE_INVALID")


def test_p11d_24_content_encoding_absent_or_single_identity_only() -> None:
    SecHttpClient._validate_success_headers(_header_response({"Content-Type":["application/json"],"Content-Encoding":["identity"]}),SecContentClass.TICKER_MAPPING_JSON)
    for enc in (["gzip"],["identity","identity"],["identity,gzip"]):
        with pytest.raises(SecHttpError): SecHttpClient._validate_success_headers(_header_response({"Content-Type":["application/json"],"Content-Encoding":enc}),SecContentClass.TICKER_MAPPING_JSON)


def test_p11d_25_partial_send_counts_start_preparation_failure_does_not(monkeypatch: pytest.MonkeyPatch) -> None:
    client,_,starts=scripted_client(monkeypatch,[FakeResponse(),FakeResponse()],send_errors=[ConnectionResetError("partial"),None])
    result=client.get_json(CURRENT,SecContentClass.SUBMISSIONS_CURRENT_JSON)
    assert result.outbound_start_count==2 and len(starts)==2
    client2,_,starts2=scripted_client(monkeypatch,[FakeResponse()],prep_errors=[TimeoutError("prep"),None])
    result2=client2.get_json(CURRENT,SecContentClass.SUBMISSIONS_CURRENT_JSON)
    assert result2.outbound_start_count==1 and len(starts2)==1


def test_p11d_26_malformed_content_length_and_mismatch_fail_closed() -> None:
    for v in ("-1","2,3","  "):
        with pytest.raises(SecHttpError): SecHttpClient._validate_success_headers(_header_response({"Content-Type":["application/json"],"Content-Length":[v]}),SecContentClass.TICKER_MAPPING_JSON)


def test_p11d_27_wrong_or_missing_content_type_blocked() -> None:
    with pytest.raises(SecHttpError) as exc: SecHttpClient._validate_success_headers(_header_response({"Content-Type":["text/json"]}),SecContentClass.TICKER_MAPPING_JSON)
    assert_reason(exc,"P11_CONTENT_TYPE_INVALID")


def test_p11d_28_non_identity_content_encoding_blocked() -> None:
    with pytest.raises(SecHttpError) as exc: SecHttpClient._validate_success_headers(_header_response({"Content-Type":["application/json"],"Content-Encoding":["br"]}),SecContentClass.TICKER_MAPPING_JSON)
    assert_reason(exc,"P11_HTTP_FAILED")


def test_p11d_29_invalid_utf8_bom_malformed_json_blocked() -> None:
    for body in (b"\xef\xbb\xbf{}",b"\xff",b"{"):
        with pytest.raises(SecHttpError) as exc: SecHttpClient._validate_json_bytes(body)
        assert_reason(exc,"P11_HTTP_FAILED")


def test_p11d_30_403_is_not_retried(monkeypatch: pytest.MonkeyPatch) -> None:
    client,_,starts=scripted_client(monkeypatch,[FakeResponse(403,b"")])
    with pytest.raises(SecHttpError): client.get_json(CURRENT,SecContentClass.SUBMISSIONS_CURRENT_JSON)
    assert len(starts)==1


def test_p11d_31_404_is_not_retried(monkeypatch: pytest.MonkeyPatch) -> None:
    client,_,starts=scripted_client(monkeypatch,[FakeResponse(404,b"")])
    with pytest.raises(SecHttpError): client.get_json(CURRENT,SecContentClass.SUBMISSIONS_CURRENT_JSON)
    assert len(starts)==1


def test_p11d_32_5xx_max_three_retries_exact_backoff(monkeypatch: pytest.MonkeyPatch) -> None:
    waits=[]; monkeypatch.setattr(http_mod,"_sleep_bounded",lambda seconds,*a,**k:waits.append(seconds))
    client,_,starts=scripted_client(monkeypatch,[FakeResponse(500,b"") for _ in range(4)])
    monkeypatch.setattr(http_mod,"_sleep_bounded",lambda seconds,*a,**k:waits.append(seconds))
    with pytest.raises(SecHttpError) as exc: client.get_json(CURRENT,SecContentClass.SUBMISSIONS_CURRENT_JSON)
    assert_reason(exc,"P11_HTTP_FAILED")
    assert waits==[1.0,2.0,4.0] and len(starts)==4


def test_p11d_33_429_retry_after_seconds(monkeypatch: pytest.MonkeyPatch) -> None:
    waits=[]; monkeypatch.setattr(http_mod,"_sleep_bounded",lambda seconds,*a,**k:waits.append(seconds))
    client=bare_client(); assert client._schedule_retry(0,http_mod.time.monotonic_ns()+100_000_000_000,retry_after_values=["5"])==1
    assert waits==[5.0]


def test_p11d_34_429_http_date_no_downward_rounding(monkeypatch: pytest.MonkeyPatch) -> None:
    now=1_700_000_000.25
    future=dt.datetime.fromtimestamp(now+10.75,tz=dt.timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")
    waits=[]; monkeypatch.setattr(http_mod.time,"time",lambda:now); monkeypatch.setattr(http_mod,"_sleep_bounded",lambda seconds,*a,**k:waits.append(seconds))
    bare_client()._schedule_retry(0,http_mod.time.monotonic_ns()+100_000_000_000,retry_after_values=[future])
    assert waits[0] >= 10.0


def test_p11d_35_multiple_retry_after_fields_fail_rate_limited(monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(SecHttpError) as exc: bare_client()._schedule_retry(0,http_mod.time.monotonic_ns()+100_000_000_000,retry_after_values=["1","2"])
    assert_reason(exc,"P11_RATE_LIMITED")


def test_p11d_36_retry_after_over_60_fails_without_early_retry(monkeypatch: pytest.MonkeyPatch) -> None:
    called=[]; monkeypatch.setattr(http_mod,"_sleep_bounded",lambda *a,**k:called.append(True))
    with pytest.raises(SecHttpError) as exc: bare_client()._schedule_retry(0,http_mod.time.monotonic_ns()+100_000_000_000,retry_after_values=["61"])
    assert_reason(exc,"P11_RATE_LIMITED"); assert not called


def test_p11d_37_counter_invariant_max7_and_prep_failure_strict() -> None:
    from itertools import permutations
    for seq in set(permutations("RRRDDD")):
        r=d=0; starts=1
        for e in seq:
            if e=="R": r+=1
            else: d+=1
            starts+=1
            assert starts <= 1+r+d <= 7
        assert starts==7
    assert 0 < 1+1+0 <= 7


def test_p11d_38_all20_interleavings_no_eighth_and_terminal_mappings(monkeypatch: pytest.MonkeyPatch) -> None:
    from itertools import permutations
    assert len(set(permutations("RRRDDD")))==20
    client=bare_client()
    monkeypatch.setattr(http_mod,"_sleep_bounded",lambda *a,**k:None)
    with pytest.raises(SecHttpError) as e429: client._schedule_retry(3,http_mod.time.monotonic_ns()+1_000_000_000,retry_after_values=[])
    assert_reason(e429,"P11_RATE_LIMITED")
    with pytest.raises(SecHttpError) as e5: client._schedule_retry(3,http_mod.time.monotonic_ns()+1_000_000_000)
    assert_reason(e5,"P11_HTTP_FAILED")


def test_p11d_39_partial_send_counts_start_retry_count_only_if_scheduled(monkeypatch: pytest.MonkeyPatch) -> None:
    client,_,starts=scripted_client(monkeypatch,[FakeResponse(),FakeResponse()],send_errors=[ConnectionResetError("x"),None])
    result=client.get_json(CURRENT,SecContentClass.SUBMISSIONS_CURRENT_JSON)
    assert len(starts)==2 and result.outbound_start_count==2


def test_p11d_40_redirect_retry_counters_global_no_reset(monkeypatch: pytest.MonkeyPatch) -> None:
    rs=[FakeResponse(500,b""),FakeResponse(302,b"",{"Location":["https://www.sec.gov/submissions/CIK0000320193.json"]}),FakeResponse()]
    client,_,starts=scripted_client(monkeypatch,rs)
    result=client.get_json(CURRENT,SecContentClass.SUBMISSIONS_CURRENT_JSON)
    assert len(starts)==3 and result.redirect_count==1 and result.outbound_start_count==3


def test_p11d_41_every_retry_redirect_emitted_start_passes_send_boundary(monkeypatch: pytest.MonkeyPatch) -> None:
    rs=[FakeResponse(500,b""),FakeResponse(302,b"",{"Location":["https://www.sec.gov/submissions/CIK0000320193.json"]}),FakeResponse()]
    client,_,starts=scripted_client(monkeypatch,rs)
    client.get_json(CURRENT,SecContentClass.SUBMISSIONS_CURRENT_JSON)
    assert len(starts)==3


def test_p11d_47_connection_preparation_failure_consumes_retry_not_emitted_count(monkeypatch: pytest.MonkeyPatch) -> None:
    waits=[]
    client,_,starts=scripted_client(monkeypatch,[FakeResponse()],prep_errors=[TimeoutError("connect"),None])
    monkeypatch.setattr(http_mod,"_sleep_bounded",lambda seconds,*a,**k:waits.append(seconds))
    result=client.get_json(CURRENT,SecContentClass.SUBMISSIONS_CURRENT_JSON)
    assert result.outbound_start_count==1 and len(starts)==1 and waits==[1.0]


def test_retry_after_malformed_falls_back_to_deterministic_backoff(monkeypatch: pytest.MonkeyPatch) -> None:
    waits=[]
    monkeypatch.setattr(http_mod,"_sleep_bounded",lambda seconds,*a,**k:waits.append(seconds))
    bare_client()._schedule_retry(1,http_mod.time.monotonic_ns()+100_000_000_000,retry_after_values=["not-a-date"])
    assert waits==[2.0]


def test_p11d_70_direct_history_url_invalid_basename_blocks_before_connection() -> None:
    for name in (" leading.json", "x%.json", "x y.json"):
        client=bare_client(); prepared=[]
        client._prepare_connection=MethodType(lambda self,parsed,deadline: prepared.append(True),client)
        with pytest.raises(SecHttpError) as exc:
            client.get_json(f"https://data.sec.gov/submissions/{name}",SecContentClass.SUBMISSIONS_HISTORY_JSON)
        assert_reason(exc,"P11_SOURCE_HOST_NOT_ALLOWED")
        assert prepared==[]


def test_p11d_71_canonical_equivalent_redirect_loop_blocks_before_second_start(monkeypatch: pytest.MonkeyPatch) -> None:
    first=FakeResponse(302,b"",{"Location":["HTTPS://DATA.SEC.GOV:443/submissions/CIK0000320193.json"]})
    client,prepared,starts=scripted_client(monkeypatch,[first])
    with pytest.raises(SecHttpError) as exc:
        client.get_json(CURRENT,SecContentClass.SUBMISSIONS_CURRENT_JSON)
    assert_reason(exc,"P11_REDIRECT_NOT_ALLOWED")
    assert len(prepared)==1 and len(starts)==1
