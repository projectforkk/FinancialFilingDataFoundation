# 219 — P11-D Discovery Candidate Ordering Preflight STOP

Status: **STOP — P11-ISSUE-042 OPEN / NO NEW CANDIDATE / P11-D IMPLEMENTATION CLOSED**

Context:

P11-ISSUE-041 already stopped candidate `702ec64ab327929d65b624e387316bea813ef22f`.

During Design-First remediation preflight, an additional material public-API inconsistency was found before freezing another candidate.

## P11-ISSUE-042

`SecDiscoveryCandidate` is declared:

`@dataclass(frozen=True, slots=True, order=True)`

while semantic fields include optional values:

- `report_date: str | None`;
- `primary_doc_description: str | None`.

Python dataclass-generated ordering compares fields lexicographically. For candidates sharing earlier fields, `<` may therefore compare `None` with `str`, which raises `TypeError` rather than providing a total order.

This automatic ordering is also unnecessary and conflicts with the separately frozen canonical discovery output ordering:

`(filing_date ASC, accession_number ASC)`.

Leaving `order=True` would expose an unsafe public ordering contract and permit implementations/callers to sort by a different field sequence than the canonical discovery contract.

## Required remediation

Before the next candidate freeze:

1. remove generated dataclass ordering from `SecDiscoveryCandidate`;
2. retain equality/hash semantics on semantic `compare=True` fields;
3. retain `submission_source_urls = field(compare=False)` so provenance stays outside equality/hash;
4. require every discovery sort to use the explicit canonical key `(filing_date, accession_number)`;
5. add focused tests proving optional fields cannot affect/order-crash discovery sorting and provenance remains excluded;
6. preserve all HTTP/security/rate/schema semantics unchanged.

## Verdict

# STOP

P11-ISSUE-042 is OPEN.

No new P11-D candidate may be frozen until ISSUE-041 and ISSUE-042 are both remediated.

P11-D implementation remains NOT AUTHORIZED.
P11 provider production remains CLOSED.