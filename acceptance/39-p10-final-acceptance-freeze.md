# 39 — P10 Final Acceptance Freeze

Status: **FROZEN — P10-N INDEPENDENT ACCEPTANCE ONLY**

Phase: P10 — Codex Dynamic Research Integration
Gate: P10-M — Acceptance Freeze

P10-N must use the exact P10-M freeze commit recorded by the subsequent P10-N authorization. No P10-N command may execute source from main, active, or another worktree.

## 1. Frozen design / production / review identity

Core design baseline:

668269e87774730ade03afb4b7564256671eb31f

P10 production source/test candidate:

d8e7d81b4bb5a4f06cead9eba0e2d09884094676

P10-G integration instruction candidate:

3a805a8f333ac20770d6aec1c8285d93993d18fc

Integration exact Git-blob SHA256:

ef10406c9957f7a68a9af001c913deef0a057e166100a2d852c0c8fcd2c46296

Formal Code Review:

development/119-p10-l-formal-code-review-result.md = PASS

Formal review result commit:

157c9309a9e1c78baab08a0ab77bd3e7408facd8

Any later change to design/24, design/25, acceptance/38, P10 production/tests, integration instruction, or this frozen acceptance package invalidates the freeze.

## 2. Frozen runtime identity

Project root:

D:\Codex\FinancialFilingDataFoundation

Main runtime:

D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe

Observed: Python 3.14.9 / 64-bit ARM64.

P8 dedicated runtime:

D:\Codex\FinancialFilingDataFoundation\runtimes\ffdf-mcp-2.3.0\.venv\Scripts\python.exe

Observed Python: Python 3.12.14 / 64-bit AMD64 runtime on ARM64 host.

P8 accepted server version: p8-local-mcp-v1

P8 exact 11 tools:

~~~
ffdf_list_documents
ffdf_get_document
ffdf_search_document
ffdf_read_pages
ffdf_list_sections
ffdf_list_tables
ffdf_get_table
ffdf_list_raw_facts
ffdf_get_fact
ffdf_get_evidence
ffdf_get_validation
~~~

P8 runtime lock:

runtime-locks/mcp-2.3.0-py312-win-amd64.lock.txt

SHA256:

8e958b8abcfd9b2de829451ffc253932fa26bb473f73837484b75b1019f092ec

P9 public contract:

~~~
p9_version=p9-review-overlay-v1
policy_version=p9-review-policy-v1
resolution_schema_version=p9-review-resolution-v1
resolved_view_schema_version=p9-resolved-view-v1
~~~

Main runtime must continue to report the external mcp SDK absent.

## 3. Exact candidate source binding

Independent Acceptance detached worktree:

D:\Codex\FinancialFilingDataFoundation\worktrees\acceptance\p10-n-<freeze-shortsha>

Every P10 Python/test command must set:

~~~
PYTHONPATH=<detached-acceptance-worktree>\src
PYTHONDONTWRITEBYTECODE=1
PYTHONIOENCODING=utf-8
~~~

Forbidden:

- shared main source;
- active P10 source;
- another review/acceptance worktree source;
- editable/install of FFDF merely for P10.

## 4. Frozen acceptance package

Harness:

acceptance/p10_independent_acceptance_harness.py

Pre-freeze SHA256:

d2504b73f951069d0fa5320fe1bd7296b95083c8f123481574f4a7935e811b3e

Size: 24005 bytes.

Immutable-base manifest:

acceptance/p10-base-immutability-manifest.json

SHA256:

ae176a49858caabb45e525fbeb9b99eec23e4b5f649dfa584ebe4656c2dba003

Entry count: 47.

Fixture manifest:

acceptance/p10-fixtures/manifest.json

SHA256:

345a00660a5e6150d2c1e547133cb9eb28aa39987d77010ce57f8f70f3d6cc3a

Fixture count: 8.

The P10-M freeze commit must contain exactly these acceptance-package bytes. P10-N must independently rehash them before execution.

## 5. Frozen runtime spec fixtures

| Fixture | SHA256 | Size | Purpose |
| --- | --- | ---: | --- |
| spec-a.md | 3c825c79422edac120f45b5c196d4a7e5105298d31df609f6ae3dab1abf09121 | 639 | table/page provenance |
| spec-b.md | abc8ecb590d87945d31969584ee8c0c530f43c25d9b90d3f8a25bbfd81a97f07 | 717 | RawFact/evidence provenance |
| live-cn.md | 309fe14ab1fb41a8feae96e1d35d69c085d391afbcb39b99acbb63636fe6fe10 | 1697 | live CN P8/P9 COMPLETE |
| missing.md | 43a8d6a797d6b8997b9c650bdbfe97a79a385b6556db98fb0207132316f7cf35 | 446 | missing filing |
| visual.md | 03ff96ace5bdba80c86296afc1e72fb296aae29cb639ef5d05236d29ca83743e | 575 | visual capability |
| drift.md | add924f9ce435ba526f2f7977ad4f7bce02be858cc15bee86b5205b23aa9f56b | 286 | spec drift |
| unresolved.md | 7bc6a18f0b1726a980ecaafdbfd53c75ce589d92e458ec8251cd368db91035e0 | 640 | unresolved unit |
| corrupt-p9.md | 67bc7b16a5e9bac01dd822a3438301b13d7c48f04a45fdc657d60817bd50d3e2 | 611 | corrupt P9 |

The reasoning host must read each relevant frozen spec completely before selecting research operations.

No fixed question/company/period/report/valuation mapping may be added to P10 production or integration instruction to satisfy these fixtures.

## 6. Immutable accepted base

Manifest:

acceptance/p10-base-immutability-manifest.json

Exact manifest SHA256:

ae176a49858caabb45e525fbeb9b99eec23e4b5f649dfa584ebe4656c2dba003

It freezes 47 files covering:

- CN/HK source PDFs;
- canonical P2 registry.sqlite;
- CN/HK P3;
- CN/HK P4;
- CN/HK P5;
- CN/HK P6;
- CN/HK P7;
- P8 live catalog;
- P8 acceptance catalog;
- P8 runtime lock;
- existing CN/HK P9 live review state.

Source PDF identities:

~~~
CN 5299f4940e2ce4e91084b73dc457d558b9d335fa76fbfee6227e4254eb7f4a30
HK 70f529984a87ef7f46d9e1db26bb9ef27eef9c01d29c59aabf69e557b479a6a0
~~~

Canonical P2 Registry SHA256:

cffb184430875f76ec52149c632842c02e840ce578fed4a048cf2993823e0e01

P8 live/acceptance catalog SHA256:

e493f2f6a951007c1e5ac932268796d35d33386760f4503d48ff0a7f7a148cdc

P10-N precheck and postcheck must both validate all 47 entries.

## 7. Acceptance mutable workspace

Use only:

D:\Codex\FinancialFilingDataFoundation\workspace\p10-n\<freeze-shortsha>

The harness pre phase requires this path to be fresh/nonexistent and creates it.

All acceptance run state must remain inside it:

- copied frozen specs;
- isolated review roots;
- output/ledger/validation artifacts;
- result summaries.

Do not reuse P10-I/J/K development workspaces as acceptance results.

## 8. Windows pytest basetemps

Use fresh single-character basetemps:

~~~
D:\Codex\FinancialFilingDataFoundation\worktrees\t\a
D:\Codex\FinancialFilingDataFoundation\worktrees\t\b
~~~

If either already exists, preserve it whole first under:

~~~
workspace/scratch/p10-n-preserved-a-before-<freeze-shortsha>
workspace/scratch/p10-n-preserved-b-before-<freeze-shortsha>
~~~

Do not delete historical basetemp evidence.

## 9. Precheck harness command

After the detached worktree and exact source binding are set:

~~~
D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe -B ^
  <detached-acceptance-worktree>\acceptance\p10_independent_acceptance_harness.py ^
  --phase pre ^
  --project-root D:\Codex\FinancialFilingDataFoundation ^
  --source-root <detached-acceptance-worktree> ^
  --work-root D:\Codex\FinancialFilingDataFoundation\workspace\p10-n\<freeze-shortsha> ^
  --mcp-python D:\Codex\FinancialFilingDataFoundation\runtimes\ffdf-mcp-2.3.0\.venv\Scripts\python.exe ^
  --report D:\Codex\FinancialFilingDataFoundation\workspace\p10-n\<freeze-shortsha>-precheck.json
~~~

Required: status=PASS.

Precheck independently verifies:

- exact candidate source binding;
- frozen 47-file base;
- frozen fixture bytes;
- P10 source/integration/core-design drift = none;
- integration exact Git-blob SHA;
- P8 server/tool/runtime-lock identity;
- P9 public contract;
- production security/future-scope absence;
- critical raw CLI subprocess behavior;
- P10 performance gates.

## 10. Fresh focused / full test commands

Focused P10:

~~~
D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe -B -m pytest tests\unit\research -q -p no:cacheprovider --basetemp D:\Codex\FinancialFilingDataFoundation\worktrees\t\a
~~~

Full P0-P10:

~~~
D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe -B -m pytest tests\unit -q -p no:cacheprovider --basetemp D:\Codex\FinancialFilingDataFoundation\worktrees\t\b
~~~

Both must execute from the detached acceptance worktree with detached PYTHONPATH.

Expected minimum current counts:

~~~
research >= 136 passed
full unit >= 444 passed
~~~

Any failure blocks acceptance.

## 11. Frozen performance gates

Limits:

~~~
freeze-spec <= 2.0 s
verify-spec <= 2.0 s
build-context <= 2.0 s
validate-ledger <= 5.0 s
spec bundle input total <= 10 MiB
~~~

Pre-freeze preview observed:

~~~
freeze_spec_s=0.0003774
verify_spec_s=0.0002972
build_context_s=0.0025167
validate_ledger_s=0.0024399
~~~

Preview report SHA256:

99184eba12feb2c2c8ee068f1cd7b9674c359a96bbbd9d921ff1e57c57e7f6ce

Preview evidence is not Independent Acceptance evidence. P10-N must rerun fresh.

## 12. Dynamic Spec A/B protocol

The reasoning host must:

1. read the complete copied inputs/spec-a.md;
2. freeze/verify it;
3. derive information need from the spec;
4. choose P8 tools according to that need;
5. create/validate a P10 ledger;
6. write results/dynamic-a.json;
7. repeat independently for the complete inputs/spec-b.md;
8. use the same P10 production candidate;
9. verify bundle hashes differ;
10. verify selected tool sets materially differ.

Expected provenance classes:

- A: P8_RAW_DIRECT table/page claim;
- B: P8_RAW_DIRECT fact/evidence claim.

Do not pre-map Spec A or Spec B to tools in P10 production/integration instruction.

Each result summary must have exactly these required semantic fields:

~~~json
{
  "status": "PASS",
  "spec_bundle_hash": "...",
  "tools_selected": ["..."],
  "ledger_validation": "PASS",
  "output_keys": ["..."]
}
~~~

Persist each actual ledger and validation under the acceptance work root.

## 13. Live COMPLETE protocol

Primary live filing:

~~~
market=CN
ticker=600519
fiscal_year=2024
filing_type=ANNUAL
document_sha256=5299f4940e2ce4e91084b73dc457d558b9d335fa76fbfee6227e4254eb7f4a30
~~~

Target RawFact:

9b3e2e441e6730c0f3c979816dd764dcb4bf70e6cde16caae9e3897733b9a015

Required P5 period evidence:

~~~
table_id=9d9d4afeb104cbcfade4847423919c7b9c60be2efef1011bb4651beb11268075
cell_id=561a43ea9a394dc90fedd52f8a14d279d22147ba52ccabf9a9c61847ec074d0b
page_no=6
text=2024
~~~

P10-ISSUE-007 is mandatory:

- construct isolated P9 review store at its final acceptance path with accepted prepare_review_overlay;
- do not copy/move existing P9 stores;
- inspect generated task;
- only if supported/evidence-grounded, submit SET_PERIOD=2024;
- materialize through accepted P9 API;
- validate the generated snapshot through accepted loader.

Frozen submission metadata:

~~~
reviewer_type=CODEX
reviewer_id=p10-independent-acceptance
reviewed_at=2026-11-04T12:00:00+09:00
justification=P10 Independent Acceptance isolated review: same-table P5 cell explicitly identifies period 2024 for the target raw fact.
~~~

Required final live behavior:

~~~
run_status=COMPLETE
raw_period=null
effective_period=2024
raw_numeric_value_changed=false
base_validation_status=REVIEW_REQUIRED
resolved_validation_status=REVIEW_REQUIRED
review_required_data_usable_for_claim=true
resolved_reuse_eligible=false
canonical_reuse_eligible=false
evidence_ledger_validation=PASS
~~~

Evidence ledger minimum:

- one P8_RAW_DIRECT claim;
- one P9_DURABLE_RESOLVED claim.

Write results/live.json with the above fields plus selected P8 tools, P9 operations, generated resolution ID, and generated overlay-set hash.

Unrelated unresolved review issues must not be force-closed.

## 14. Negative capability protocol

Use copied frozen negative specs and fresh acceptance-local state.

Required results:

~~~
K1 = P10_DATA_PREPARATION_REQUIRED
K2 = P10_VISUAL_CAPABILITY_REQUIRED
K3 = P10_UPSTREAM_INVALID
K4 = P10_RESEARCH_SPEC_CHANGED
K5 = P10_REVIEW_UNRESOLVED
~~~

Required safety booleans:

~~~
k1_download_attempted=false
k2_guessed_visual=false
k3_silent_raw_fallback=false
k4_silent_refresh=false
k5_guessed_semantic=false
~~~

K3:

- build a separate fresh isolated P9 store through accepted APIs;
- prove valid durable provenance PASS before tamper;
- tamper only the isolated negative snapshot;
- fresh validation must block as P10_UPSTREAM_INVALID.

K4 mutates only the acceptance-workspace copy of drift.md.

K5 requires raw unit null and no supported unit-resolution task; do not infer or guess a unit.

Write results/negative.json with exact K1–K5 reasons and safety booleans.

## 15. Postcheck harness command

After dynamic/live/negative acceptance runs:

~~~
D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe -B ^
  <detached-acceptance-worktree>\acceptance\p10_independent_acceptance_harness.py ^
  --phase post ^
  --project-root D:\Codex\FinancialFilingDataFoundation ^
  --source-root <detached-acceptance-worktree> ^
  --work-root D:\Codex\FinancialFilingDataFoundation\workspace\p10-n\<freeze-shortsha> ^
  --report D:\Codex\FinancialFilingDataFoundation\workspace\p10-n\<freeze-shortsha>-postcheck.json
~~~

Required: status=PASS.

Postcheck verifies:

- all 47 frozen base files unchanged;
- Spec A/B hashes differ;
- Spec A/B tool sets differ;
- both dynamic ledgers PASS;
- live COMPLETE;
- raw numeric unchanged;
- REVIEW_REQUIRED usability boundary;
- non-canonical reuse boundary;
- K1–K5 exact negative reasons;
- no silent fallback/refresh/guessing;
- no hidden chain-of-thought artifact filename.

## 16. CLI acceptance matrix

Fresh full unit execution includes tests/unit/research/test_research_cli.py and must independently pass all frozen design/24 Section 31 and acceptance/38 Section 2.1 cases:

- four success commands;
- one-line canonical JSON;
- LF-only output;
- parser JSON / exit 2;
- malformed/non-UTF8/non-object/extra/missing input handling;
- 16 MiB input bound;
- spec-first precedence;
- catalog path boundary;
- context/review-root boundary;
- domain reason preservation;
- fixed internal failure envelope;
- no traceback/help prose.

The precheck harness separately repeats critical raw subprocess cases.

## 17. Immutability / no hidden reasoning

Before/after immutable-base checks must pass.

Only the isolated acceptance workspace may mutate.

No acceptance artifact may store hidden chain-of-thought.

Permitted evidence artifacts:

- frozen spec copies;
- P8/P9 tool/state summaries;
- ledgers;
- validation results;
- structured research outputs;
- result summaries;
- test/harness reports;
- hashes/timings.

## 18. Acceptance verdict

Allowed verdicts:

PASS / FAIL / BLOCKED

PASS requires all acceptance/38 mandatory items and this freeze package to pass.

No design/production/fixture/harness fix may be made inside the detached acceptance worktree.

Any required candidate change invalidates this freeze and returns to Design-First.

On PASS record:

- exact detached acceptance HEAD;
- pre/post immutable hashes;
- focused/full test counts;
- dynamic A/B hashes/tool selections;
- live resolution/overlay IDs;
- K1–K5;
- final PASS.

P11, Research MCP production, and Semantic Resolver production remain outside P10 acceptance scope.
