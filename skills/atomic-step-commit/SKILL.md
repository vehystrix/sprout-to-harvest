---
name: atomic-step-commit
description: >-
  Use when a subagent has modified files and must leave a resumable,
  reviewable step result on the implementation branch.
---
# Atomic Step Commit

The final report in this sequence must use `agent-handoff` and the persisted
report must follow `final-report-format`. Include changed files, validation
evidence, commit hash, repository state, blockers, and resume instructions.

The final sequence for file-modifying work is:

```text
validate -> commit -> persist commit status -> report
```

Commit only the assigned step and required tests. Record the commit hash
and validation evidence. If safe rollback requires multiple commits, use a
temporary child branch and merge the verified result into the implementation
branch before returning.
