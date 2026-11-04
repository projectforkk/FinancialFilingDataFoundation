# 117 — P10-K Negative Capability Gates Evidence

Status: **PASS — P10-K CLOSED**

Phase:
`P10 — Codex Dynamic Research Integration`

Gate:
`P10-K — Negative Capability Gates`

Authorization:
`development/116-p10-k-negative-gates-authorization.md`

Authorization commit:
`4521294`

Current design baseline:
`668269e87774730ade03afb4b7564256671eb31f`

Workspace:
`D:\\Codex\\FinancialFilingDataFoundation\\workspace\\research-runs\\p10-k`

No production/tests/design code was modified during P10-K.

## 1. Frozen negative specs

All five runtime specs were frozen and completely read before their cases ran.

### K1 missing filing

```text
raw_sha256=b2dfe4067dfa86de42fe0a951a31548c1ea3f88782ed619f6f7f872a3bc98806
bundle_hash=1070ca028ce8836168b0cad028197beccff40ae0cb6eb0c2b943af7b47a654fd
```

### K2 visual-only

```text
raw_sha256=b3a5ad80e3c40df841921d16546a6d68c55cb7c62b3fac5fa14c8e542e14af60
bundle_hash=010e3dfff0293d33a4cb1354eb4bde574e65aabc0855702551153e628bf1b417
```

### K3 corrupt P9

```text
raw_sha256=8e38f56e95e48aa3d7789493354b3cde4190c1ef385aa618eda85650aaf2d7c7
bundle_hash=57856f5275ebd9eddece675af598672fbde45e1028c452146c1dcb9e9386d3f8
```

### K4 spec drift

```text
raw_sha256_before=b5928b8dcdcfbb0cf3003e9211b792c4dbe2f28a0fd44d16dfee4527b3f4b2bc
bundle_hash=dda5c24c994820c02ca8264a378bd861c22984e2c6d187e2c8b9935491721e11
raw_sha256_after_mutation=8fe2df13145277cbcbca0e2de2168b97c44e964744ff3d52fa0adf6deb2c42ec
```

### K5 unresolved semantic

```text
raw_sha256=306151f8c96790bfe482cc370393346cd50a950247f69fccc08977e642620252
bundle_hash=c81ab52c4c03e7bb440b2465853479d156afdc139eb1c75baf618c013a994bba
```

## 2. K1 — Missing filing

Frozen requirement:

```text
market=CN
ticker=P10_MISSING_FIXTURE
fiscal_year=2099
filing_type=ANNUAL
```

Accepted P8 query:

`ffdf_list_documents`

Exact matching documents:

`0`

Result:

`P10_DATA_PREPARATION_REQUIRED`

Verified:

```text
download_attempted=false
substitute_company_used=false
substitute_period_used=false
claimed_never_disclosed=false
```

No acquisition or substitution occurred.

Output SHA256:

`c1061e3cca3283d6f05170c75cd9fed931fa75a1a4f5468bc8655ef643c4fb9c`

## 3. K2 — Visual-only requirement

Frozen task asked for exact visual font color/emphasis styling on page 6.

Structured P8 page text was available.

P10-D capability manifest reported:

`PDF_VISUAL_EVIDENCE=UNAVAILABLE`

Result:

`P10_VISUAL_CAPABILITY_REQUIRED`

Verified:

```text
structured_page_text_available=true
visual_font_color_proven=false
arbitrary_pdf_opened=false
research_mcp_used=false
fake_run_local_verified_created=false
```

No screenshot/render/PDF visual workaround was introduced.

Output SHA256:

`a0e4dc6abd1ac0b183e26db296eb899e53b7ceaaf0332d4cfba84d7eac7fd517`

## 4. K3 — Corrupt P9 store

A fresh isolated P9 store was constructed through accepted P9 APIs under:

`workspace/research-runs/p10-k/review-corrupt`

Before tamper:

- supported/evidence-grounded `SET_PERIOD` resolution created;
- isolated resolution ID:
  `6732547b1ff94150c5ae7cd8ca76d6ca83ab771fb9b37df81667144b78fc470a`;
- isolated overlay:
  `0703f0bb53a88f26eb65d0e1e76fe0df0d834d74989a1f0305f36fea3b34b26a`;
- P10 durable ledger validation:
  `PASS`.

Valid-before output SHA256:

`db8b2bcc89fdd9961aea7bc3b7f371cafd8209eb2bee57a3163ecf55de7d0b44`

Only the isolated negative snapshot's:

`resolution_report.json`

was then corrupted.

Fresh P10 ledger validation result:

`P10_UPSTREAM_INVALID`

Verified:

`silent_raw_fallback=false`

The corrupt overlay was not ignored.

Negative output SHA256:

`ef0674efced9b5f8ba956bb779991b53e2e34f0af69b50b046157dcdede2c5d8`

## 5. K4 — Mid-run spec mutation

The drift spec was frozen and verified.

One byte-sequence mutation was then appended to the runtime spec.

Fresh verification returned exactly:

`P10_RESEARCH_SPEC_CHANGED`

Verified:

`silent_refresh=false`

The frozen bundle was not refreshed or silently replaced.

Output SHA256:

`aa23d94b83e04a0844206ff8802fe3c17d31ba4b129fa5b9c8daa3d0ac3600d9`

## 6. K5 — Unresolved semantic requirement

Target live RawFact:

`9b3e2e441e6730c0f3c979816dd764dcb4bf70e6cde16caae9e3897733b9a015`

Observed raw unit:

`null`

A fresh accepted P9 review overlay was prepared under the P10-K workspace.

Available supported review task:

```text
reason_code=RAW_PERIOD_COVERAGE_LOW
supported_actions=SET_PERIOD
```

Supported unit-resolution task:

`NONE`

Therefore the required effective unit remained unresolved.

Result:

`P10_REVIEW_UNRESOLVED`

Verified:

```text
guessed_unit=false
fake_verified_unit_created=false
```

Output SHA256:

`0f6c4f0a0ecb7aca3bfa1bae09221e80e853c655b48c8363b9f63c63a645e226`

## 7. Accepted-base immutability

Accepted P8 base before:

`80d0d84ea1e9349ac18d6446bf7380a2a9cc62bd28bcd552c9759cca2b0cb6ad`

Accepted P8 base after:

`80d0d84ea1e9349ac18d6446bf7380a2a9cc62bd28bcd552c9759cca2b0cb6ad`

`P8_UNCHANGED=True`

Source P9 live state before:

`e3cde7918a5225e6cc541db949464783a06e5989f9d65bcbf68cac8abc181371`

Source P9 live state after:

`e3cde7918a5225e6cc541db949464783a06e5989f9d65bcbf68cac8abc181371`

`P9_SOURCE_UNCHANGED=True`

Only project-local negative fixtures were created/tampered.

## 8. Negative-gate summary

```text
K1 missing filing
  PASS -> P10_DATA_PREPARATION_REQUIRED

K2 visual-only requirement
  PASS -> P10_VISUAL_CAPABILITY_REQUIRED

K3 corrupt P9
  valid before tamper = PASS
  PASS -> P10_UPSTREAM_INVALID
  silent fallback = false

K4 spec drift
  PASS -> P10_RESEARCH_SPEC_CHANGED
  silent refresh = false

K5 unresolved semantic requirement
  PASS -> P10_REVIEW_UNRESOLVED
  guessed semantic value = false
```

All design/25 P10-K required negative cases passed.

## 9. Branch state

During final audit the active branch remained clean and matched remote.

No tracked production/test/design mutation occurred during execution.

## 10. Verdict

# PASS

P10-K Negative Capability Gates is closed.

A separate explicit authorization may begin:

`P10-L — Performance / Artifact Size`

P10-L and later remain closed until separately authorized.

Research MCP production, Semantic Resolver production, and P11 production remain closed.
