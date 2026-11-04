# FFDF Research Integration

Status: **P10 v1 integration instruction**

This file defines how a reasoning host consumes accepted FFDF capabilities.

It is **not** a research specification.

It must not replace, summarize into fixed business rules, or silently override the current runtime research specification supplied for a research run.

## 1. Start every research run from the current specification

Before using FFDF data:

1. freeze the caller-provided runtime research specification with P10;
2. verify the frozen specification bytes;
3. read the frozen specification completely;
4. derive the current run's information needs from that specification;
5. select FFDF capabilities from those information needs.

Do not use a fixed question number, report section, company, period, valuation method, or investment rule to choose tools.

If the research specification changes after freeze:

`P10_RESEARCH_SPEC_CHANGED`

Do not continue the same research context with silently changed instructions.

## 2. Responsibility boundary

### P8 — Raw Data & Evidence

P8 provides deterministic read-only access to accepted local filing artifacts, including:

- document discovery and metadata;
- page text;
- deterministic sections;
- reconstructed tables;
- source-preserving raw facts;
- first-class evidence;
- validation reports/issues.

P8 raw facts remain raw facts.

Do not relabel `ffdf_get_fact` as a semantic or resolved fact.

### P9 — Durable Reviewed Decision Store

P9 stores supported, evidence-grounded reviewed decisions.

P9 may be used only when:

- the current research need actually requires semantic clarification;
- the review task/action is supported;
- required evidence is available;
- the interpretation is explicit and defensible;
- the action does not correct the raw numeric value or raw metric text.

P9 is not a generic fixer for every `REVIEW_REQUIRED` document.

### P10 — Dynamic Research Integration

P10 provides deterministic plumbing for:

- runtime-spec freeze/verification;
- research-context identity;
- capability manifest;
- FFDF evidence-ledger validation;
- deterministic machine CLI.

P10 does not perform financial reasoning and does not call remote AI.

### Reasoning host

The reasoning host is responsible for:

- understanding the current frozen research specification;
- deriving information needs dynamically;
- choosing accepted P8/P9 operations;
- interpreting evidence for the current run;
- deciding whether current evidence is sufficient;
- producing the research output requested by the runtime specification.

## 3. Data availability first

Use accepted P8 document discovery to confirm that the required filing exists in the current catalog.

If a required filing is absent:

`P10_DATA_PREPARATION_REQUIRED`

Do not:

- download it through P10;
- substitute another period;
- substitute another company;
- assume an adjacent filing is equivalent;
- claim non-disclosure merely because the local catalog lacks the filing.

Acquisition/data preparation is an upstream workflow.

## 4. Query priority

For each information need, use this decision order:

```text
valid durable P9 reviewed state exists?
  yes -> use the validated durable state
  no  -> inspect exact P8 raw/structured evidence

P8 structured evidence sufficient for the current claim?
  yes -> current-run use with explicit provenance
  no  -> is a supported evidence-grounded P9 review possible?
          yes -> optional controlled P9 review
          no  -> explicit unresolved/capability gap
```

Tool choice is driven by the information need, not by a fixed question-to-tool map.

## 5. REVIEW_REQUIRED is not DATA_UNUSABLE

A document-level `REVIEW_REQUIRED` status does not make all evidence unusable.

The reasoning host may still inspect and use, where appropriate:

- RawFact;
- Evidence;
- Table;
- Page Text;
- validation issue context;
- valid P9 effective fields.

However:

- do not claim the document is canonically reusable when it is not;
- do not hide unresolved semantic fields;
- do not derive a value that requires semantics that remain unresolved.

## 6. Current-run use classes

### P9_DURABLE_RESOLVED

Use only when the exact P9 resolution/snapshot identity validates.

This may be reusable in later runs only under the accepted P9 identity rules.

### P8_RAW_DIRECT

Use for source-preserving raw values/text/evidence.

Do not pretend unknown period, unit, scope, or value role is known.

### RUN_LOCAL_STRUCTURED_VERIFIED

Use when P8 structured evidence is sufficient for the reasoning host to make an explicit current-run interpretation, but the interpretation is not a durable P9 resolution.

It must remain:

- `durable=false`;
- `canonical_reuse_eligible=false`;
- traceable to FFDF provenance.

### UNRESOLVED

Use when evidence is insufficient, conflicting, or semantically ambiguous.

Do not use an unresolved claim where a unique interpretation is required.

## 7. Raw extraction defects

If structured evidence shows that the underlying P5/P6 extraction is wrong:

```text
STOP semantic/review workaround
-> classify as upstream raw extraction defect
-> return to the relevant parser Design-First correction
-> rerun affected upstream stages
```

Do not use P9 to change:

- raw numeric value;
- parsed numeric value;
- raw metric name.

## 8. Derived calculations

A derived calculation is allowed only when every required operand is ready for derived use.

At minimum verify:

- numeric value;
- period;
- value role;
- required unit/dimension;
- required scope;
- no unresolved conflict;
- complete provenance;
- operation compatibility.

Do not treat a run-local derived result as canonical reusable parsed data.

Do not infer standalone quarter values from incompatible cumulative values.

Do not perform a derived calculation when required semantics remain unresolved.

## 9. Provenance

Every FFDF-supported research claim required by the run should have a P10 evidence-ledger entry.

FFDF provenance may reference accepted identities such as:

- document SHA256;
- physical page;
- table ID;
- raw fact ID;
- evidence ID;
- P9 resolution ID;
- P9 overlay-set hash.

Validate the ledger against the current:

- frozen specification;
- research context;
- P8 catalog;
- P9 snapshot identity where applicable.

A natural-language statement that the model "saw" something is not provenance.

## 10. External runtime sources

A runtime research specification may require information outside FFDF, for example market, industry, policy, competitor, or other external information.

Such sources are separate from FFDF provenance.

When a separate runtime-source record is used, mark its source class as:

`EXTERNAL_RUNTIME_SOURCE`

Rules:

- do not label an external source as P8/P9 evidence;
- do not put external-source entries into the P10-E FFDF ledger v1;
- keep external-source citations/provenance in the research output or a separate runtime-source record;
- do not use an external source to support a P9 resolution unless a future accepted P9 design explicitly permits it.

If the current research requirement needs an external source that is unavailable:

`P10_EXTERNAL_SOURCE_REQUIRED`

Do not guess.

## 11. Capability manifest

P10 v1 declares these capabilities available:

- `P8_RAW_QUERY`;
- `P8_PAGE_TEXT`;
- `P8_TABLE_STRUCTURED`;
- `P8_EVIDENCE`;
- `P8_VALIDATION`;
- `P9_REVIEW`;
- `P9_RESOLVED_VIEW`.

P10 v1 declares these unavailable:

- `PDF_VISUAL_EVIDENCE`;
- `SEMANTIC_RESOLVER`;
- `CANONICAL_METRIC_LAYER`;
- `P11_SEC_PROVIDER`.

Do not pretend an unavailable capability is implemented.

Typical explicit gaps include:

- `P10_DATA_PREPARATION_REQUIRED`;
- `P10_VISUAL_CAPABILITY_REQUIRED`;
- `P10_SEMANTIC_CAPABILITY_REQUIRED`;
- `P10_CANONICAL_CAPABILITY_REQUIRED`;
- `P10_EXTERNAL_SOURCE_REQUIRED`;
- `P10_UPSTREAM_INVALID`;
- `P10_REVIEW_UNRESOLVED`;
- `P10_INCOMPATIBLE_REQUIREMENT`.

## 12. Structured evidence is insufficient when visual proof is required

P10 v1 has no PDF visual renderer.

If structured P8/P9 evidence cannot prove the required relationship because of missing/conflicting visual layout, table crop, cross-page presentation, or other visual-only evidence:

`P10_VISUAL_CAPABILITY_REQUIRED`

Do not:

- fake a run-local verified interpretation;
- open arbitrary PDF paths through P10;
- assume the future Research MCP already exists.

## 13. Deterministic P10 CLI

P10's machine CLI supports only:

- `freeze-spec`;
- `verify-spec`;
- `build-context`;
- `validate-ledger`.

It is a deterministic adapter over accepted P10 APIs.

It does not proxy P8 business queries or P9 mutations.

P8/P9 calls remain through their accepted interfaces.

## 14. Execution source boundary

Every P10 Python command must bind the exact candidate/worktree source:

```powershell
$env:PYTHONPATH="<exact-candidate-worktree>\src"
```

Do not editable-install FFDF into the shared main virtual environment merely to execute P10.

All FFDF-owned temporary/workspace state must remain inside the canonical project root.

## 15. No guessing / no silent fallback

When evidence, capability, or upstream state is insufficient:

- return the appropriate explicit gap/error;
- preserve unresolved state;
- identify what evidence/capability is missing.

Never:

- fabricate missing values;
- silently substitute periods/scopes;
- silently ignore corrupt P9 state;
- silently downgrade provenance;
- silently claim canonical reuse;
- use an unsupported capability as if it were available.

## 16. Hidden reasoning is not a project artifact

Research outputs may contain conclusions, calculations, evidence references, and concise rationale required by the runtime specification.

Do not persist hidden chain-of-thought as an FFDF project artifact.

P10 evidence artifacts record identities, provenance, validation, and explicit run results—not private model reasoning traces.

## 17. This instruction must remain business-rule neutral

This file describes FFDF integration behavior only.

The current runtime research specification remains the source for:

- what questions to answer;
- what entities/periods to study;
- what output structure to produce;
- what terminology to use;
- what calculations or valuation approaches are requested;
- what external sources are required.

Changing those research requirements must not require changing P10 production or this integration instruction.
