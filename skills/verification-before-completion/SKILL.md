---
name: verification-before-completion
description: Only use when explicitly invoked
# description: "Use when deciding whether an implementation, test step, documentation change,
#   or workflow phase is complete."
user-invocable: false
disable-model-invocation: true
---
# Verification Before Completion

Return verification results through `agent-handoff`; persisted reports
must use its YAML schema. `VERIFIED` requires executable evidence in the
handoff; missing or malformed handoff fields require `BLOCKED`. The final
plan-level result must additionally follow `final-report-format`.

Require evidence before a success status. Prefer focused executable tests,
then relevant typecheck/build/lint commands, then broader validation.
Compare results with the assigned acceptance criteria and requirement matrix.

Report the command, result, and remaining risk. Use `INCOMPLETE` or
`BLOCKED` when evidence is missing; never infer success from changed
files alone.
