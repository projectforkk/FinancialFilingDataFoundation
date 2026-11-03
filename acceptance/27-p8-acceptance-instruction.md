# 27 — P8 Independent Acceptance Instruction

状态：**DESIGN BASELINE — P8 ACCEPTANCE**

最终 verdict：PASS / FAIL / BLOCKED。

Mandatory:

1. frozen candidate HEAD stable
2. P0–P7 regression PASS
3. prior accepted source/tests zero unintended diff
4. main venv仍无 mcp package
5. dedicated runtime = Python 3.12.14 AMD64 + exact mcp==2.3.0
6. dedicated runtime lock `mcp-2.3.0-py312-win-amd64.lock.txt` reproducible
7. official SDK stdio server starts
8. protocol negotiation succeeds
9. exact 11 tool names
10. no arbitrary path tool
11. no shell/sql/python execution tool
12. no HTTP/SSE listener
13. no network/AI imports/calls
14. catalog paths project-root-relative only
15. absolute/traversal catalog paths blocked
16. duplicate document identities blocked
17. upstream P3/P5/P6/P7 loaders validated
18. upstream corruption returned as execution error, not validation BLOCKED
19. list documents deterministic
20. search/read pages deterministic
21. sections deterministic
22. table list/detail deterministic
23. fact list/detail deterministic
24. evidence exact relation
25. validation report/issues deterministic
26. argument/pagination/payload limits
27. CN live tool calls PASS
28. HK live tool calls PASS
29. upstream artifacts/catalog unchanged
30. cold startup/connect/list-tools <=15s without document bundle load
31. first trusted bundle load per document <=15s
32. warm representative business calls meet tool performance gates
33. ffdf_list_documents is catalog-only and does not claim unvalidated P7 status

Acceptance must not modify:
- production
- tests
- design
- config
- dependencies/runtime

P8 PASS 后才允许 P9 Review Overlay。
