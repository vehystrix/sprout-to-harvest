---
name: verification-before-completion
description: "MUST use before completing a task. Verify task completion based on executable evidence"
user-invocable: true
disable-model-invocation: false
---

# Verification Before Completion

When invoked directly by the user outside an orchestrated run, produce no
persisted workflow artifacts (`agent-handoff` reports or `.agent-work/` state);
report results conversationally instead. When delegated from the orchestrator
or a role agent, persist outputs exactly as this skill and its format skills describe.

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

## Related skills

- `agent-handoff`
- `final-report-format`
