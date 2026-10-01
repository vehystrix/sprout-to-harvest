---
name: s2h-implementation
description: Only use when explicitly invoked
# description: "Use when implementing one bounded step from an approved plan while
#   preserving repository conventions, scope, and validation evidence."
user-invocable: false
disable-model-invocation: true
---
# Implementation Execution

Read the assigned context and the current checkpoint before editing.
Persist step progress using `s2h-step-status-format`. Make the smallest change that
satisfies the step. 
Preserve unrelated work, follow local patterns, and run the narrowest
meaningful validation first.

Record changed files, tests, warnings, blockers, and the resulting commit.
Do not expand scope to unrelated cleanup.

## Related skills

- `s2h-step-status-format`
