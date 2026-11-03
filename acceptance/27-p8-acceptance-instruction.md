# 27 — P8 Independent Acceptance Instruction

状态：**DESIGN BASELINE — P8 ACCEPTANCE**

最终 verdict：PASS / FAIL / BLOCKED。

Mandatory:

1. frozen candidate HEAD stable
2. P0–P7 regression PASS
3. prior accepted source/tests zero unintended diff
4. main venv仍无 mcp package
5. dedicated runtime = Python 3.12.14 AMD64 + exact mcp==2.3.0
6. dedicated runtime lock `mcp-2.3.0-py312-win-amd64.lock.txt` reproducible; `.gitattributes` enforces LF; Git blob SHA256 == clean checkout working-tree SHA256 == documented lock SHA256
7. dedicated MCP runtime executes tracked stdlib server-registration/SDK-boundary harness without adding pytest to the runtime lock
8. official SDK stdio server starts
9. protocol negotiation succeeds
10. exact 11 tool names
11. no arbitrary path tool
12. no shell/sql/python execution tool
13. no HTTP/SSE listener
14. no network/AI imports/calls
15. catalog paths project-root-relative only
16. absolute/traversal catalog paths blocked
17. duplicate document identities blocked
18. upstream P3/P5/P6/P7 loaders validated
19. upstream corruption returned as execution error, not validation BLOCKED
20. list documents deterministic
21. search/read pages deterministic
22. sections deterministic
23. table list/detail deterministic
24. fact list/detail deterministic
25. evidence exact relation
26. validation report/issues deterministic
27. argument/pagination/payload limits
28. CN live tool calls PASS
29. HK live tool calls PASS
30. upstream artifacts/catalog unchanged
31. cold startup/connect/list-tools <=15s without document bundle load
32. first trusted bundle load per document <=20s
33. warm representative business calls meet tool performance gates
34. ffdf_list_documents is catalog-only and does not claim unvalidated P7 status

Windows pytest execution rule:
- use short project-root-local basetemp under `D:\Codex\FinancialFilingDataFoundation\workspace\t\p8\<acceptance-run>`；
- do not place pytest basetemp beneath the detached review/acceptance worktree；
- do not create FFDF-owned sibling temp directories under `D:\Codex`；
- basetemp contents are ignored disposable test execution state only.

Acceptance must not modify:
- production
- tests
- design
- config
- dependencies/runtime

P8 PASS 后才允许 P9 Review Overlay。
