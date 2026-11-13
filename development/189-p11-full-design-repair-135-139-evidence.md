# P11 Full-Design Repair 135–139 Development Evidence

Status: **DEVELOPMENT EVIDENCE ONLY / READY FOR FRESH EXACT-CANDIDATE DESIGN-CODE REVIEW**

This document records the repair candidate and development verification. It is not
formal acceptance, not a merge authorization, and not a P11 DONE record.

## 1. Exact authority and candidate identity

- Repository: `projectforkk/FinancialFilingDataFoundation`
- Branch: `task/p11-sec-rebuild-development`
- Worktree: `D:\Codex\FinancialFilingDataFoundation\worktrees\active\p11-sec-rebuild-development`
- Corrected design baseline: `09e3174b7e19a60cc5955862670fac8931af67db`
- Repair worktree starting HEAD: `4bf644374af3a0585453379fcc185d6464105776`
- Prior reviewed production candidate: `c7bcfa6bd3b01a769cc5e3063378c68c7a4dd67b`
- Independent full-design review: `development/188-p11-full-design-code-consistency-review-3.md`
- Independent review commit: `882b76cb082875b6867e3b409674038192675142`
- Final P11 production candidate: `55fc575cdaaeebd8b686ce76120978c714ca1a28`
- Candidate commits: `c60159cf8df02df77b85fc0a7a61238a533ebead` plus the
  legacy-history compatibility repair in `55fc575cdaaeebd8b686ce76120978c714ca1a28`

The intermediate `c60159cf` was not carried forward as the final candidate:
the first real Apple FY run exposed official legacy history rows with blank
`primaryDocument` values. The final candidate retains those official source
bytes, skips only non-addressable legacy rows, and fails closed when an
incomplete periodic row is near the requested fiscal slot.

## 2. Repair disposition

- P11-ISSUE-135: **IMPLEMENTED** — persisted official submissions/history bytes
  are decoded, rehashed, independently reparsed, merged, and used to derive
  candidate equality, state, and selected accession.
- P11-ISSUE-136: **IMPLEMENTED** — all listed history chunks are processed with
  deterministic ordering and a bounded count; discovery no longer stops after
  the first historical match; all source bodies used by the observation are
  retained.
- P11-ISSUE-137: **IMPLEMENTED** — SEC summary/company-context retrieval uses
  the verified SEC bundle and re-verifies the raw package, evidence, Registry,
  discovery observation, and P7 identity chain, including cached access.
- P11-ISSUE-138: **IMPLEMENTED** — Inline XBRL and XBRL instance roles, facts,
  contexts, units, dimensions, continuations, and exclusions require authentic
  namespaces; generic lookalikes are not promoted to structured facts.
- P11-ISSUE-139: **DESIGN-CORRECTED / IMPLEMENTED** — explicit `6-K` and
  `6-K/A` are deferred from P11 v1 and deterministically rejected before US
  provider execution. No accession, package, Registry, or P8 entry is created.

No remote AI/API call was added. Original SEC documents remain immutable.

## 3. Exact-candidate verification

All commands below were run from the final candidate worktree with
`PYTHONPATH=<worktree>\src` and the project-local Python runtime.

Focused P11-ISSUE-135..139 suite:

```text
tests/unit/us_sec/test_full_design_repair_135_139.py
33 passed in 1.47s
EXIT=0
```

US SEC and MCP catalog regression:

```text
tests/unit/us_sec tests/unit/mcp/test_catalog_service.py
193 passed in 18.98s
EXIT=0
```

Full unit regression, covering the accepted P0–P10 behavior together with the
P11 unit suite:

```text
tests/unit
703 passed in 84.21s
EXIT=0
```

Static checks:

- `python -m compileall -q src`: **PASS / EXIT=0**
- `git diff --check`: **PASS / EXIT=0**
- Candidate worktree status immediately before this evidence document:
  **clean**

## 4. Apple FY 2025 isolated live smoke

Production-shaped CLI run on the exact candidate:

```text
ffdf ingest --market US --cik 320193 --ticker AAPL --year 2025 --period FY
```

Receipt:

- accession: `0000320193-25-000079`
- package SHA-256:
  `079185e72f20bd4fc1a2a19b2c57430390b2fb5482403b51752525a0264ff131`
- structured Raw Facts: `1,131`
- discovery source bodies retained: `2`
  (`CIK0000320193.json` and `CIK0000320193-submissions-001.json`)
- XSD members: `1`
- XBRL linkbase members: `4`
- JPEG/static asset fetches: `0`
- P7 validation: `PASS`
- P7 blocking issues: `0`
- P8 catalog: `ADDED`
- `research_ready`: `true`
- isolated smoke root:
  `D:\ffdf-p11-full-design-repair-live-20261113-v4`
- traced acquisition root:
  `D:\ffdf-p11-full-design-repair-live-trace-20261113-v2`

The traced acquisition made 10 SEC requests and contained no JPEG, JPG, PNG,
GIF, or SVG request. The package contained the primary HTML document, one XSD,
four XBRL linkbase resources, and the filing summary.

## 5. Governance boundary

- Formal Test Plan created: **NO**
- Formal acceptance executed: **NO**
- Main merge performed: **NO**
- P11 DONE claimed: **NO**
- Source/test modified after final candidate freeze: **NO**
- Work after candidate freeze: documentation-only evidence preparation

Next required action:

```text
CHATGPT FRESH FULL EXACT-CANDIDATE DESIGN/CODE REVIEW OF 55fc575cdaaeebd8b686ce76120978c714ca1a28
```
