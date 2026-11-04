# 229 - P11-ISSUE-044 Evidence Serialization Correction

Status: **CORRECTION - CANDIDATE 760a4aa INELIGIBLE FOR FORMAL REVIEW / DESIGN CONTRACT BYTES UNCHANGED**

Historical candidate:
`760a4aa60a93c3d42570f7640798b80eaaad187e`

Finding:
`development/228-p11-d-outbound-start-invariant-amendment-evidence.md` in that candidate was serialized through a PowerShell double-quoted here-string. Markdown backticks were interpreted as PowerShell escapes, corrupting several evidence lines and leaving the literal `$sha` instead of the design SHA256.

Impact:

- `design/31-p11-d-http-discovery-contract.md` in `760a4aa...` is technically intact;
- no source/test/integration/runtime-lock file was affected;
- the evidence artifact is not audit-quality, therefore `760a4aa...` MUST NOT be used as the exact detached design-review candidate;
- no force-push or history rewrite is permitted.

Remediation:

- rewrite development/228 as literal UTF-8 with exact Markdown backticks and exact contract SHA256;
- record this correction in a new commit;
- freeze the resulting new exact candidate and authorize a fresh detached review against that candidate only.

P11-D implementation remains STOPPED.
P11 provider production remains CLOSED.
