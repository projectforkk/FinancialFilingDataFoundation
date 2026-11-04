# 231 - P11-D ISSUE-044 Hash-Basis Review STOP

Status: **STOP - CANDIDATE 63620f7 INELIGIBLE / GOVERNANCE EVIDENCE AMBIGUITY / DESIGN CONTRACT SEMANTICS INTACT**

Reviewed candidate:
`63620f7360a91702016781e915ce71fac8fef848`

Authorization:
`development/230-p11-d-issue044-final-design-review-authorization.md`

Fresh detached worktree:
`D:\Codex\FinancialFilingDataFoundation\worktrees\review\p11-d-design-63620f7`

Finding:

The evidence recorded SHA256 `497407adb368f8abbbe12afa1096fb7d9674d2fdb1a5778c8468b8f4b52dfaf9` under the ambiguous label "Amended contract SHA256". On Windows checkout, Git line-ending normalization produces CRLF working-tree bytes whose SHA256 is `9e69eeee67df34f695fc8657ddb6b018cb19be3d252dac1a737f13b3d7f79eb7`, while the canonical Git blob bytes hash to the recorded `497407...` value.

The recorded value is therefore correct for canonical repository content, but the evidence failed to state the hash basis explicitly. Exact detached review must not infer whether a content hash means working-tree bytes or canonical Git blob bytes.

Impact:

- `design/31-p11-d-http-discovery-contract.md` semantics are unchanged and remain coherent;
- ISSUE-044 counter/provenance/security semantics are not reopened;
- no production/test/integration/runtime-lock bytes are implicated;
- candidate `63620f7...` is ineligible for formal PASS solely because the evidence hash basis is ambiguous.

Required remediation:

- relabel the development/228 hash explicitly as **Canonical Git-blob SHA256**;
- freeze a new exact candidate without changing design/31;
- conduct a new fresh detached review that hashes `git show <candidate>:design/31...` bytes, not checkout-transformed working-tree bytes.

# STOP

P11-D implementation remains STOPPED.
P11 provider production remains CLOSED.
