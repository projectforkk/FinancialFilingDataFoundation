from __future__ import annotations

import json
from dataclasses import replace

import pytest

from financial_filing_data_foundation.sec import (
    SecContentClass,
    SecDiscoveryCandidate,
    SecDiscoveryError,
    SecHttpResponse,
    discover_sec_filings,
    load_sec_ticker_rows,
)

CIK="0000320193"
CURRENT=f"https://data.sec.gov/submissions/CIK{CIK}.json"


def response(url: str, obj: object) -> SecHttpResponse:
    body=json.dumps(obj,separators=(",",":"),sort_keys=True).encode()
    return SecHttpResponse(url,url,200,"application/json",body,1,0)


class FakeClient:
    def __init__(self, mapping: dict[str, object]) -> None:
        self.mapping=mapping
        self.calls: list[tuple[str,SecContentClass]]=[]
    def get_json(self,url: str,content_class: SecContentClass) -> SecHttpResponse:
        self.calls.append((url,content_class))
        if url not in self.mapping:
            raise AssertionError(f"unexpected fetch {url}")
        return response(url,self.mapping[url])


def arrays(rows: list[dict[str,object]]) -> dict[str,list[object]]:
    keys=("accessionNumber","filingDate","reportDate","form","primaryDocument","primaryDocDescription","isXBRL","isInlineXBRL")
    return {k:[row[k] for row in rows] for k in keys}


def row(accession="0000320193-25-000001", filing="2025-01-31", report="2024-12-31", form="10-K", primary="aapl-20240928.htm", desc="Annual", x=1, ix=1):
    return {"accessionNumber":accession,"filingDate":filing,"reportDate":report,"form":form,"primaryDocument":primary,"primaryDocDescription":desc,"isXBRL":x,"isInlineXBRL":ix}


def current(rows_: list[dict[str,object]], files: list[dict[str,object]] | None=None, cik: object="320193") -> dict[str,object]:
    return {"cik":cik,"filings":{"recent":arrays(rows_),"files":[] if files is None else files}}


def discover(client: FakeClient, **kwargs):
    args=dict(cik="320193",target_base_forms=("10-K",),filing_date_from="2024-01-01",filing_date_to="2025-12-31")
    args.update(kwargs)
    return discover_sec_filings(client,**args)


def assert_reason(exc: pytest.ExceptionInfo[SecDiscoveryError], reason: str) -> None:
    assert exc.value.reason_code==reason


def test_p11d_48_current_only_discovery() -> None:
    client=FakeClient({CURRENT:current([row()])})
    out=discover(client)
    assert len(out)==1 and out[0].cik==CIK and out[0].base_form=="10-K"
    assert [u for u,_ in client.calls]==[CURRENT]


def test_p11d_49_historical_shard_discovery() -> None:
    name=" CIK0000320193-submissions-001.json"; url=f"https://data.sec.gov/submissions/{name}"
    files=[{"name":name,"filingFrom":"2023-01-01","filingTo":"2024-12-31","filingCount":1}]
    old=row("0000320193-24-000001","2024-02-01","2023-12-31")
    client=FakeClient({CURRENT:current([],files),url:arrays([old])})
    out=discover(client)
    assert [x.accession_number for x in out]==[old["accessionNumber"]]
    assert [u for u,_ in client.calls]==[CURRENT,url]


def test_p11d_50_non_overlapping_history_not_fetched() -> None:
    name="old.json"; files=[{"name":name,"filingFrom":"2020-01-01","filingTo":"2020-12-31","filingCount":0}]
    client=FakeClient({CURRENT:current([row()],files)})
    discover(client)
    assert [u for u,_ in client.calls]==[CURRENT]


def test_p11d_51_required_parallel_arrays_all_exist_equal_lengths() -> None:
    bad=current([row()]); del bad["filings"]["recent"]["form"]
    client=FakeClient({CURRENT:bad})
    with pytest.raises(SecDiscoveryError) as exc: discover(client)
    assert_reason(exc,"P11_SUBMISSIONS_INVALID")
    bad2=current([row()]); bad2["filings"]["recent"]["form"].append("10-K")
    with pytest.raises(SecDiscoveryError): discover(FakeClient({CURRENT:bad2}))


@pytest.mark.parametrize("bad",[True,False,"1",1.0,2,-1,None])
def test_p11d_52_xbrl_flags_accept_exact_integer_0_1_only(bad: object) -> None:
    r=row(x=bad)
    with pytest.raises(SecDiscoveryError): discover(FakeClient({CURRENT:current([r])}))


def test_p11d_53_candidate_xbrl_fields_are_non_null_bool() -> None:
    out=discover(FakeClient({CURRENT:current([row(x=0,ix=1)])}))
    assert type(out[0].is_xbrl) is bool and type(out[0].is_inline_xbrl) is bool
    assert out[0].is_xbrl is False and out[0].is_inline_xbrl is True


def test_p11d_54_no_generated_rich_ordering_explicit_sort_handles_optional_nulls() -> None:
    a=SecDiscoveryCandidate(CIK,"0000320193-25-000001","10-K","10-K",False,"2025-01-01",None,"a.htm",None,True,True,(CURRENT,))
    b=SecDiscoveryCandidate(CIK,"0000320193-25-000002","10-K","10-K",False,"2025-01-02","2024-12-31","b.htm","B",True,True,(CURRENT,))
    with pytest.raises(TypeError): _=a < b
    assert sorted([b,a],key=lambda x:(x.filing_date,x.accession_number))==[a,b]


def test_p11d_55_historical_filing_count_equals_shard_row_count() -> None:
    name="h.json"; url=f"https://data.sec.gov/submissions/{name}"
    files=[{"name":name,"filingFrom":"2024-01-01","filingTo":"2024-12-31","filingCount":2}]
    client=FakeClient({CURRENT:current([],files),url:arrays([row("0000320193-24-000001","2024-02-01")])})
    with pytest.raises(SecDiscoveryError) as exc: discover(client)
    assert_reason(exc,"P11_SUBMISSIONS_INVALID")


def test_p11d_56_duplicate_identical_descriptors_collapse_even_extra_metadata_differs() -> None:
    name="h.json"; url=f"https://data.sec.gov/submissions/{name}"
    base={"name":name,"filingFrom":"2024-01-01","filingTo":"2024-12-31","filingCount":1}
    files=[dict(base,extra="a"),dict(base,extra="b")]
    client=FakeClient({CURRENT:current([],files),url:arrays([row("0000320193-24-000001","2024-02-01")])})
    discover(client)
    assert [u for u,_ in client.calls].count(url)==1


def test_p11d_57_same_descriptor_name_conflict_fails_before_overlap_filter() -> None:
    name="old.json"
    files=[
        {"name":name,"filingFrom":"2020-01-01","filingTo":"2020-12-31","filingCount":0},
        {"name":name,"filingFrom":"2020-01-01","filingTo":"2020-12-31","filingCount":1},
    ]
    client=FakeClient({CURRENT:current([row()],files)})
    with pytest.raises(SecDiscoveryError) as exc: discover(client)
    assert_reason(exc,"P11_SUBMISSIONS_INVALID")
    assert len(client.calls)==1


def test_p11d_58_descriptor_input_reorder_same_canonical_fetch_order() -> None:
    descs=[
        {"name":"b.json","filingFrom":"2024-01-01","filingTo":"2024-12-31","filingCount":0},
        {"name":"a.json","filingFrom":"2024-01-01","filingTo":"2024-06-30","filingCount":0},
    ]
    urls={f"https://data.sec.gov/submissions/{x['name']}":arrays([]) for x in descs}
    orders=[]
    for files in (descs,list(reversed(descs))):
        client=FakeClient({CURRENT:current([],files),**urls}); discover(client); orders.append([u for u,_ in client.calls[1:]])
    assert orders[0]==orders[1]==["https://data.sec.gov/submissions/a.json","https://data.sec.gov/submissions/b.json"]


@pytest.mark.parametrize("bad",[True,"320193",320193.0,None])
def test_p11d_59_ticker_cik_str_requires_json_integer_not_bool_string_float(bad: object) -> None:
    obj={"0":{"cik_str":bad,"ticker":"aapl","title":"Apple"}}
    with pytest.raises(SecDiscoveryError) as exc: load_sec_ticker_rows(FakeClient({"https://www.sec.gov/files/company_tickers.json":obj}))
    assert_reason(exc,"P11_SUBMISSIONS_INVALID")
    ok=load_sec_ticker_rows(FakeClient({"https://www.sec.gov/files/company_tickers.json":{"0":{"cik_str":320193,"ticker":" aapl ","title":"Apple"}}}))
    assert ok==(("AAPL",CIK),)


def test_p11d_60_duplicate_identical_accession_dedupes() -> None:
    r=row(); out=discover(FakeClient({CURRENT:current([r,r])}))
    assert len(out)==1


def test_p11d_61_semantic_equal_current_history_union_sorted_unique_provenance() -> None:
    name="h.json"; url=f"https://data.sec.gov/submissions/{name}"; r=row()
    files=[{"name":name,"filingFrom":"2025-01-01","filingTo":"2025-12-31","filingCount":1}]
    out=discover(FakeClient({CURRENT:current([r],files),url:arrays([r])}))
    assert len(out)==1 and out[0].submission_source_urls==tuple(sorted((CURRENT,url)))


def test_p11d_62_provenance_excluded_from_equality_and_hash() -> None:
    a=SecDiscoveryCandidate(CIK,"0000320193-25-000001","10-K","10-K",False,"2025-01-31","2024-12-31","a.htm",None,True,True,("a",))
    b=replace(a,submission_source_urls=("b",))
    assert a==b and hash(a)==hash(b)


def test_p11d_63_duplicate_conflicting_accession_fails_closed() -> None:
    a=row(); b=row(primary="different.htm")
    with pytest.raises(SecDiscoveryError) as exc: discover(FakeClient({CURRENT:current([a,b])}))
    assert_reason(exc,"P11_SUBMISSIONS_INVALID")


def test_p11d_64_current_input_order_does_not_change_canonical_output() -> None:
    a=row("0000320193-25-000002","2025-02-02"); b=row("0000320193-25-000001","2025-01-01")
    outs=[]
    for rows_ in ([a,b],[b,a]):
        outs.append(discover(FakeClient({CURRENT:current(rows_)})))
    assert outs[0]==outs[1]
    assert [x.accession_number for x in outs[0]]==[b["accessionNumber"],a["accessionNumber"]]


def test_p11d_65_ticker_rows_sorted_and_ambiguity_retained() -> None:
    url="https://www.sec.gov/files/company_tickers.json"
    obj={
        "0":{"cik_str":2,"ticker":"z","title":"Z"},
        "1":{"cik_str":3,"ticker":"a","title":"A"},
        "2":{"cik_str":1,"ticker":"a","title":"A2"},
    }
    rows=load_sec_ticker_rows(FakeClient({url:obj}))
    assert rows==(("A","0000000001"),("A","0000000003"),("Z","0000000002"))


def test_p11d_66_target_accession_exact_match_or_not_found() -> None:
    r=row(); client=FakeClient({CURRENT:current([r])})
    out=discover(client,target_accession=r["accessionNumber"]); assert len(out)==1
    with pytest.raises(SecDiscoveryError) as exc: discover(FakeClient({CURRENT:current([r])}),target_accession="0000320193-25-999999")
    assert_reason(exc,"P11_FILING_NOT_FOUND")


def test_p11d_67_no_silent_amendment_supersession() -> None:
    original=row("0000320193-25-000001",form="10-K")
    amended=row("0000320193-25-000002",form="10-K/A")
    out=discover(FakeClient({CURRENT:current([amended,original])}))
    assert [(x.accession_number,x.amended) for x in out]==[(original["accessionNumber"],False),(amended["accessionNumber"],True)]


def test_p11d_68_discovery_never_fetches_p11e_package_assets() -> None:
    client=FakeClient({CURRENT:current([row()])})
    discover(client)
    assert all("/Archives/" not in url and "index.json" not in url for url,_ in client.calls)
    assert all(cls in {SecContentClass.SUBMISSIONS_CURRENT_JSON,SecContentClass.SUBMISSIONS_HISTORY_JSON} for _,cls in client.calls)


def test_invalid_discovery_caller_arguments_fail_before_network() -> None:
    client=FakeClient({})
    invalid=[
        dict(cik="bad",target_base_forms=("10-K",),filing_date_from="2024-01-01",filing_date_to="2025-01-01"),
        dict(cik="320193",target_base_forms=(),filing_date_from="2024-01-01",filing_date_to="2025-01-01"),
        dict(cik="320193",target_base_forms=("BAD",),filing_date_from="2024-01-01",filing_date_to="2025-01-01"),
        dict(cik="320193",target_base_forms=("10-K",),filing_date_from="2025-01-01",filing_date_to="2024-01-01"),
        dict(cik="320193",target_base_forms=("10-K",),filing_date_from="2024-01-01",filing_date_to="2025-01-01",target_accession="bad"),
    ]
    for kwargs in invalid:
        with pytest.raises(ValueError): discover_sec_filings(client,**kwargs)
    assert client.calls==[]

def test_primary_document_safe_basename_rejects_paths_controls_query_fragment() -> None:
    for primary in ("../x.htm","dir/x.htm","x\\y.htm","x.htm?y=1","x.htm#f","x\x00.htm",".",".."):
        with pytest.raises(SecDiscoveryError):
            discover(FakeClient({CURRENT:current([row(primary=primary)])}))
