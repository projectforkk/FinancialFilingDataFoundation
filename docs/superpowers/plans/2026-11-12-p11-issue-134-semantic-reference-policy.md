# P11-ISSUE-134 Semantic XBRL Reference Acquisition Repair Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restore deterministic acquisition of filing-local XBRL dependencies from semantic `link:schemaRef` and `link:linkbaseRef` constructs without allowing ordinary browser references or SEC index extensions to authorize downloads.

**Architecture:** Keep the repair at the SEC archive-member selection/fetch boundary in `us_sec/acquisition.py`. Extract semantic references only from the accepted primary/XBRL member constructs, normalize and bind targets to the same accession index, and resolve newly accepted XBRL members through a bounded set-based queue. Parser, package SHA, provenance, MIME, path, size, and schema/version contracts remain unchanged.

**Tech Stack:** Python standard library `HTMLParser`/`xml.etree.ElementTree`, existing `SecAcquirer`, `SecPackageStore`, `SecMemberRole`, `parse_sec_package`, pytest, deterministic fake SEC transport.

**Spec:** `design/26-p11-sec-provider-design.md` §7.3, `design/33-p11-post-acceptance-design-correction.md` DC-05, and the P11-ISSUE-134 repair request.

## Global Constraints

- Do not modify or amend `606e744c99c7d9b46d94415058c6ccc780165a0b`.
- Keep ordinary browser/static references unselected and unfetched; do not add static MIME types to the global allowlist.
- Do not sweep `.xml`, `.xsd`, or `.xbrl` files by filename extension or SEC index type alone.
- A semantic target must come from an explicit XBRL construct, be present in the same accession index, and pass existing path/host/MIME/size/byte validation.
- Dependency resolution is bounded, cycle-safe, duplicate-safe, deterministic, and fetches each target at most once.
- Preserve recognized EX-101 metadata selection, `FilingSummary.xml`, `OTHER` XML isolation, package SHA/provenance, raw-store immutability, and all version constants.
- No parser/package/schema production changes are authorized unless a test proves they are technically required; this repair should remain in acquisition plus US SEC tests.
- After the new production candidate is frozen, no source/test changes are allowed; the next commit is documentation-only evidence.
- Do not create a Formal Test Plan, enter Formal Acceptance, merge main, or claim P11 DONE.
- Execute inline in this worktree; do not create or dispatch agents.

## Review Focus

- A namespaced `link:schemaRef` or `link:linkbaseRef` must select a same-accession target even when its SEC index `type` is `text.gif`, `XML`, or blank; T134-01 and T134-02 pin this.
- A generic HTML hyperlink to `.xml` must remain unselected even when the file is in `index.json`; T134-03 pins this.
- Primary browser assets, including JPEG, PNG, GIF, CSS, JS, WOFF2, and SVG, must remain unselected; T134-04 pins this.
- A non-inline primary must acquire one generic-typed XBRL instance through the supported semantic-reference path and produce `XBRL_INSTANCE_PRIMARY` facts without duplicates; T134-05 pins this.
- Repeated/cyclic semantic dependencies must terminate with one fetch per target; T134-07 pins this.

### Task 1: T134 deterministic regression suite

**Files:**
- Create: `tests/unit/us_sec/test_semantic_reference_acquisition.py`
- Preserve: `tests/unit/us_sec/test_acquisition_reference_policy.py`

**Interfaces:**
- Consumes: current `SecAcquirer.acquire`, `_select_archive_members`, `SecPackageStore`, `SecMemberRole`, and `parse_sec_package`.
- Produces: failing tests that require semantic construct extraction independent of index `type`, bounded dependency discovery, exact provenance, and the existing ISSUE-133 static-asset gate.

- [ ] **Step 1: Add T134-01 through T134-08 tests before production changes**

Use one deterministic fake SEC transport with call recording and forbidden static names. Cover:

- `link:schemaRef` to an `.xsd` whose index type is `text.gif`; assert one fetch, `XBRL_SCHEMA`, package inclusion, and static siblings absent.
- `link:linkbaseRef` to a presentation/linkbase member whose index type is generic; assert one fetch and no browser siblings.
- ordinary `<a href="unrelated.xml">` with generic/XML/blank index type; assert no fetch/package member.
- JPEG, PNG, GIF, CSS, JS, WOFF2, and decorative SVG all present in the index; assert zero fetches and no package members.
- a primary with no Inline XBRL facts that reaches one generic-typed XBRL instance through the supported semantic-reference path; parse the resulting package and assert `XBRL_INSTANCE_PRIMARY`, positive logical facts, one logical fact universe, and existing validation compatibility.
- recognized EX-101 metadata selects its member without any semantic reference.
- duplicate and cyclic A→B / B→A references terminate, include each member once, and fetch each URL once.
- semantic-member source URL is the exact `archive_member_url` for package CIK/accession/name; package SHA and reload manifest remain valid.

Also include unsafe/external semantic references and preserve existing `test_sec_acquirer_downloads_primary_and_xbrl_members_incrementally`.

- [ ] **Step 2: Run the focused new suite in RED state**

Run:

```powershell
& $py -m pytest -q tests/unit/us_sec/test_semantic_reference_acquisition.py --basetemp D:\t\p11-134-red
```

Expected: failures are specifically the generic-index `schemaRef`/`linkbaseRef` and non-inline instance cases because the current implementation gates HTML references on semantic index metadata; static/generic-hyperlink negatives must not fail for the wrong reason.

### Task 2: Minimal semantic dependency repair

**Files:**
- Modify: `src/financial_filing_data_foundation/us_sec/acquisition.py`
- Test: `tests/unit/us_sec/test_semantic_reference_acquisition.py` and existing US SEC acquisition tests

**Interfaces:**
- Consumes: Task 1's semantic construct fixtures and existing package/path/MIME validation.
- Produces: `_extract_semantic_xbrl_references(...)` or an equivalent private helper, a metadata-independent `_select_archive_members(...)`, and bounded acquisition of accepted semantic dependencies.

- [ ] **Step 1: Extract only explicit semantic XBRL constructs**

Recognize `link:schemaRef` and `link:linkbaseRef` with `xlink:href`/`href` from the primary HTML using a namespaced tag-aware parser. Recognize the same local constructs from accepted XBRL XML members using the XBRL linkbase namespace. Do not collect generic `href`, `src`, or ordinary anchors. Normalize fragments/query handling through the existing archive path policy and discard external/unsafe references.

- [ ] **Step 2: Remove the incorrect index-type gate**

For a validated semantic reference, select the canonical target whenever it exists in the same accession's `items_by_name`, regardless of its `type` value. Keep recognized EX-101 metadata selection as an independent OR path and keep `FilingSummary.xml` unchanged. Do not add extension-based selection.

- [ ] **Step 3: Resolve accepted XBRL dependencies with a bounded queue**

Fetch selected members in deterministic name order, retain them by canonical name, scan only the primary and accepted XBRL-role member bodies for further semantic references, and repeat until no new target exists. The selected-name set and fetched-name map provide cycle/duplicate safety; every member still goes through exact URL, content-type, size, byte, and package provenance validation.

- [ ] **Step 4: Run focused tests GREEN**

Run the new suite and the existing provider incrementality regression. Expected: all T134 tests pass, static assets remain zero-fetch, generic XML remains excluded, semantic generic-index targets are fetched once, and the non-inline package parses as `XBRL_INSTANCE_PRIMARY` with facts.

### Task 3: Candidate verification and live evidence

**Files:**
- Modify: none after candidate freeze
- Create after freeze: `development/187-p11-issue-134-repair-evidence.md`

- [ ] **Step 1: Run the required developer suites**

Run the exact T134 policy, provider, HTTP/discovery, US SEC, full unit, P0–P10, compileall, and diff-check commands from the repair request. Record exact counts and exit codes.

- [ ] **Step 2: Run Apple live developer smoke if contact is configured**

Use an isolated disposable root with `FFDF_P11_US_DEV` absent. Record accession, complete live member inventory (`relative_name | role | content_type`), package SHA, and JPEG fetch/package absence. This is developer evidence only.

- [ ] **Step 3: Freeze one production/test candidate**

Commit only source/test changes as:

```text
fix: restore deterministic XBRL semantic reference acquisition
```

Record the exact SHA and make no further source/test changes.

- [ ] **Step 4: Write and commit documentation-only evidence**

Create `development/187-p11-issue-134-repair-evidence.md`, run final checks, commit:

```text
docs: record P11 issue 134 repair evidence
```

Verify candidate→evidence contains only the documentation path, push normally, verify remote lineage, and stop before Formal Acceptance.

## Completion Contract

- ISSUE-134 is fixed without regressing ISSUE-133.
- T134-01 through T134-06 and T134-08 pass; T134-07 is PASS if bounded recursion is implemented, otherwise N/A with an evidence rationale.
- P11-ISSUE-123–133 regression passes.
- The old candidate `606e744c...` remains unchanged and historical.
- A new exact production candidate is frozen, followed by documentation-only evidence.
- Formal Test Plan = NOT CREATED, Formal Acceptance = NOT RUN, Main merge = NOT RUN, P11 DONE = NO.
