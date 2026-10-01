---
name: s2h-atomic-step-commit
description: Only use when explicitly invoked
# description: >-
#   Use when a subagent has modified files and must leave a resumable,
#   reviewable step result on the implementation branch.
user-invocable: false
disable-model-invocation: true
---
# Atomic Step Commit

The final report in this sequence must use `s2h-handoff`. Persist it as
`reports/<phase>-<subject>-<attempt>.yaml` in the run directory per
`s2h-handoff`. Include changed files, validation evidence, commit hash,
repository state, blockers, and resume instructions.

The final sequence for file-modifying work is:

```text
validate -> commit -> persist commit status -> report
```

Commit only the assigned step and required tests. Record the commit hash
and validation evidence. If safe rollback requires multiple commits, use a
temporary child branch and merge the verified result into the implementation
branch before returning.

## Related skills

- `s2h-handoff`
- `s2h-step-status-format`
