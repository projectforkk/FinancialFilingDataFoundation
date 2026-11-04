# 130 — P10 Acceptance Harness Preview Stop — P10-ISSUE-009

Status: **STOPPED — P10-ISSUE-009 BASE MANIFEST IDENTITY AMENDMENT REQUIRED**

Phase:
P10 — Codex Dynamic Research Integration

Partial harness candidate:
9621f20d33c1d1b650bcdf1a7686b5f0b9c7c817

Preview detached worktree:
D:\Codex\FinancialFilingDataFoundation\worktrees\review\p10-issue008-harness-9621f20

Preview result:
PRECHECK PASS

## 1. What passed

P10-ISSUE-008 fixture correction worked:

- fixture_identity_source=GIT_BLOB;
- fixture manifest SHA=345a00660a5e6150d2c1e547133cb9eb28aa39987d77010ce57f8f70f3d6cc3a;
- all 8 frozen fixture SHA/size checks matched exact Git blobs;
- copied acceptance workspace inputs matched those blobs;
- P8/P9/security/performance/CLI critical prechecks passed.

## 2. New finding

The same preview reported base immutable-manifest SHA from checkout bytes:

fab2c081c448f2b7d3821d226d692f152a6495e064f034ecef6d350d798416e1

But the frozen P10-M identity is:

ae176a49858caabb45e525fbeb9b99eec23e4b5f649dfa584ebe4656c2dba003

Binary-safe Git inspection proves:

- exact candidate Git blob SHA = ae176a49858caabb45e525fbeb9b99eec23e4b5f649dfa584ebe4656c2dba003;
- detached checkout bytes differ due Git checkout filtering;
- the harness validate_manifest() still reads the checked-out manifest with Path.read_bytes().

The harness therefore validates base entries correctly but reports/uses a checkout-specific manifest byte identity instead of the frozen Git-truth identity.

## 3. Root cause

P10-ISSUE-008 fixed frozen runtime-spec fixture blobs but did not yet generalize Git-blob identity to the frozen base immutability manifest.

This is the same cross-worktree checkout-filter class of defect.

## 4. Required correction

For acceptance/p10-base-immutability-manifest.json:

- read exact candidate Git blob bytes;
- parse JSON from those blob bytes;
- report SHA from those blob bytes;
- continue validating the 47 referenced project files from their real project paths.

The 47 base files themselves remain actual immutable project-state bytes and are not replaced by Git blobs.

The acceptance freeze must also record tracked acceptance-package identities as Git blob identities where relevant.

## 5. Gate effect

Partial harness candidate 9621f20 is not eligible for formal review/freeze.

P10 production remains unchanged.

P10-N and closeout remain closed.

Required sequence:

design amendment
-> harness v2 amendment
-> targeted formal review
-> new P10-M freeze
-> new P10-N
