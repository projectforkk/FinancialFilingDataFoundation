# 71 — P9-JR3 Shell-Token Corrective Development Instruction

Status: **AUTHORIZED — P9-JR3 ONLY**

Trigger:
`development/70-p9-jr2-formal-rereview-result.md` = FAIL.

Root:
all work remains inside `D:\\Codex\\FinancialFilingDataFoundation`.

## Scope

Only correct shell command-segment detection for:

- `powershell` / `powershell.exe`
- `pwsh` / `pwsh.exe`
- `bash` / `bash.exe`
- `curl` / `curl.exe`
- `wget` / `wget.exe`

Requirements:

- bare token at command-segment start rejects；
- argument forms reject；
- command segment start is string start or after newline / `;` / `&` / `|`；
- keyword appearing only mid-sentence is not rejected solely for that token；
- keep stable security reason/message；
- retain every previous security/CLI regression。

Add direct tests for bare and at least one argument/segment form.

Run focused/full/complete contract probe/compile/scope.

After evidence, perform fresh detached review. PASS is required before P9-K.

No other production scope is authorized.
