# 121 — P10-M Acceptance Freeze Evidence

Status: **PASS — P10-M ACCEPTANCE FREEZE PACKAGE READY**

Phase:
P10 — Codex Dynamic Research Integration

Gate:
P10-M — Acceptance Freeze

Authorization:
development/120-p10-m-acceptance-freeze-authorization.md

Authorization commit:
edbc98114ded023f135c00ce44354b56c74a2a66

## 1. Frozen core identity

Core design baseline:

668269e87774730ade03afb4b7564256671eb31f

P10 production source/test candidate:

d8e7d81b4bb5a4f06cead9eba0e2d09884094676

P10-G integration instruction candidate:

3a805a8f333ac20770d6aec1c8285d93993d18fc

Integration Git-blob SHA256:

ef10406c9957f7a68a9af001c913deef0a057e166100a2d852c0c8fcd2c46296

Formal review:

development/119-p10-l-formal-code-review-result.md = PASS

Formal review result commit:

157c9309a9e1c78baab08a0ab77bd3e7408facd8

No P10 production/test, design/24, design/25, or acceptance/38 semantic change occurred during P10-M.

## 2. Frozen acceptance package

Freeze instruction:

acceptance/39-p10-final-acceptance-freeze.md

SHA256 before freeze commit:

883dcf1a98de579ef976b08193c254d3a3f9248677a3fbda578c4e3173c38138

Acceptance harness:

acceptance/p10_independent_acceptance_harness.py

SHA256:

d2504b73f951069d0fa5320fe1bd7296b95083c8f123481574f4a7935e811b3e

Size:

24005 bytes

Base immutability manifest:

acceptance/p10-base-immutability-manifest.json

SHA256:

ae176a49858caabb45e525fbeb9b99eec23e4b5f649dfa584ebe4656c2dba003

Entry count:

47

Fixture manifest:

acceptance/p10-fixtures/manifest.json

SHA256:

345a00660a5e6150d2c1e547133cb9eb28aa39987d77010ce57f8f70f3d6cc3a

Fixture count:

8

## 3. Frozen fixture hashes

~~~text
spec-a.md
3c825c79422edac120f45b5c196d4a7e5105298d31df609f6ae3dab1abf09121
639 bytes

spec-b.md
abc8ecb590d87945d31969584ee8c0c530f43c25d9b90d3f8a25bbfd81a97f07
717 bytes

live-cn.md
309fe14ab1fb41a8feae96e1d35d69c085d391afbcb39b99acbb63636fe6fe10
1697 bytes

missing.md
43a8d6a797d6b8997b9c650bdbfe97a79a385b6556db98fb0207132316f7cf35
446 bytes

visual.md
03ff96ace5bdba80c86296afc1e72fb296aae29cb639ef5d05236d29ca83743e
575 bytes

drift.md
add924f9ce435ba526f2f7977ad4f7bce02be858cc15bee86b5205b23aa9f56b
286 bytes

unresolved.md
7bc6a18f0b1726a980ecaafdbfd53c75ce589d92e458ec8251cd368db91035e0
640 bytes

corrupt-p9.md
67bc7b16a5e9bac01dd822a3438301b13d7c48f04a45fdc657d60817bd50d3e2
611 bytes
~~~

All fixture files decode as UTF-8 and contain no UTF-8 BOM.

## 4. Immutable-base coverage

The 47-entry manifest freezes:

- CN/HK source PDFs;
- canonical P2 Registry;
- CN/HK P3;
- CN/HK P4;
- CN/HK P5;
- CN/HK P6;
- CN/HK P7;
- P8 live catalog;
- P8 acceptance catalog;
- P8 runtime lock;
- existing CN/HK P9 live review state.

Key identities:

~~~text
CN source/document SHA
5299f4940e2ce4e91084b73dc457d558b9d335fa76fbfee6227e4254eb7f4a30

HK source/document SHA
70f529984a87ef7f46d9e1db26bb9ef27eef9c01d29c59aabf69e557b479a6a0

Registry SHA256
cffb184430875f76ec52149c632842c02e840ce578fed4a048cf2993823e0e01

P8 live/acceptance catalog SHA256
e493f2f6a951007c1e5ac932268796d35d33386760f4503d48ff0a7f7a148cdc

P8 runtime lock SHA256
8e958b8abcfd9b2de829451ffc253932fa26bb473f73837484b75b1019f092ec
~~~

## 5. Runtime freeze

Main runtime:

D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe

Observed:

Python 3.14.9 / ARM64 / 64-bit

P8 dedicated runtime:

D:\Codex\FinancialFilingDataFoundation\runtimes\ffdf-mcp-2.3.0\.venv\Scripts\python.exe

Observed:

Python 3.12.14 / AMD64 runtime / 64-bit

P8 exact server/tool contract remains:

p8-local-mcp-v1 / 11 read-only tools

P9 public contract remains:

~~~text
p9-review-overlay-v1
p9-review-policy-v1
p9-review-resolution-v1
p9-resolved-view-v1
~~~

## 6. Acceptance harness compile / scope

Harness compile:

PASS

git diff --check:

PASS

Core candidate diff during package authoring:

~~~text
src/tests = NONE
design/24 = NONE
design/25 = NONE
acceptance/38 = NONE
~~~

No production/design semantic mutation was needed to create the acceptance package.

## 7. Fresh precheck preview #1

Workspace:

workspace/p10-acceptance-preview-m

Result:

PASS

Report:

workspace/scratch/p10-m-precheck-preview.json

SHA256:

99184eba12feb2c2c8ee068f1cd7b9674c359a96bbbd9d921ff1e57c57e7f6ce

Observed performance:

~~~text
freeze_spec_s=0.0003774
verify_spec_s=0.0002972
build_context_s=0.0025167
validate_ledger_s=0.0024399
~~~

## 8. Fresh precheck preview #2

Independent second fresh workspace:

workspace/p10-acceptance-preview-m2

Result:

PASS

Report:

workspace/scratch/p10-m-precheck-preview2.json

SHA256:

1d4d30a3abcefe9b69232a97a620efaadd8ec9ff2e1891223c2db53aae788dd7

Observed performance:

~~~text
freeze_spec_s=0.00037080002948641777
verify_spec_s=0.0002850999590009451
build_context_s=0.002359899925068021
validate_ledger_s=0.0027216998860239983
~~~

Both preview runs independently verified:

- exact source binding;
- all 47 immutable-base entries;
- all 8 fixture bytes;
- integration Git-blob SHA;
- production/integration/core design zero drift;
- P8 11-tool/runtime-lock identity;
- P9 public contract;
- forbidden/future production absence;
- critical raw CLI subprocess behavior;
- performance gates.

These previews are freeze-package validation only, not Independent Acceptance evidence.

## 9. Postcheck preview

The postcheck was exercised with structured summaries derived only from already-PASS P10-I/J/K development evidence.

Result:

PASS

Report:

workspace/scratch/p10-m-postcheck-preview2.json

SHA256:

ff7be0e6b6576ebf761baad87f91ae647715e838b4e6cdde69896f4ccfa03601

Verified postcheck rules:

- Spec A/B hashes must differ;
- tool selections must differ;
- both dynamic ledgers PASS;
- live result COMPLETE;
- raw numeric unchanged;
- REVIEW_REQUIRED usability boundary preserved;
- canonical reuse remains false;
- K1–K5 exact reasons;
- no silent download/guess/fallback/refresh;
- no hidden reasoning artifact names;
- all 47 immutable-base entries unchanged.

This preview does not replace fresh P10-N execution.

## 10. Frozen Independent Acceptance protocol

acceptance/39 freezes:

- exact candidate/source binding;
- exact test commands;
- exact short basetemp policy;
- exact pre/post harness commands;
- exact runtime specs and hashes;
- dynamic Spec A/B host protocol;
- live isolated P9 construction per P10-ISSUE-007;
- fixed P5 period evidence;
- fixed P9 submission metadata;
- live evidence-ledger requirements;
- K1–K5 negative requirements;
- immutable-base before/after;
- performance limits;
- no hidden chain-of-thought artifact;
- PASS/FAIL/BLOCKED verdict.

The reasoning host still must read each applicable runtime spec completely and choose research operations based on the current information need. The harness does not contain fixed Spec A/B tool mappings.

## 11. Freeze semantics

The commit containing:

- acceptance/39;
- acceptance harness;
- base manifest;
- fixture manifest/files;
- this evidence;

is the P10-M freeze package commit.

A subsequent P10-N authorization must record that exact commit SHA.

Independent Acceptance must create its detached worktree from exactly that P10-M freeze commit.

Any candidate/package change after freeze invalidates the freeze.

## 12. Verdict

# PASS — P10-M ACCEPTANCE PACKAGE READY TO FREEZE

After this package is committed and pushed:

P10-M is closed.

P10-N remains closed until a separate explicit authorization records the exact freeze commit.

P11, Research MCP production, and Semantic Resolver production remain outside P10 acceptance scope.
