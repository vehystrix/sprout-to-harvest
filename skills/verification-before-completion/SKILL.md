---
name: verification-before-completion
description: "MUST use before completing a task; verify completion with executable evidence"
user-invocable: true
disable-model-invocation: false
---

# Verification Before Completion

User mode: report conversationally; no `.agent-work` artifacts or `agent-handoff`
reports. Delegated mode: persist per this skill and its format skills.
Verify only the assigned work; report defects without repairing them during verification.

Return verification results through `agent-handoff`; persisted reports
must use its YAML schema. `VERIFIED` requires executable evidence in the
handoff; missing or malformed handoff fields require `BLOCKED`. The final
plan-level result must additionally follow `final-report-format`.

Require evidence before a success status. Prefer focused executable tests,
then relevant typecheck/build/lint commands, then broader validation.
Compare results with the assigned acceptance criteria and requirement matrix.
When no executable test covers the work (documentation, configuration, or wiring changes),
use the strongest available command evidence - parse, render, lint, link-check, or diff
the artifact against each acceptance criterion directly.

Classify failures before choosing a status: an environment problem - setup missing,
permissions, unavailable tools, unreadable inputs - is `BLOCKED`; checks that ran but
left the criteria unsatisfied are `INCOMPLETE`.

Report the command, result, and remaining risk. Use `INCOMPLETE` or
`BLOCKED` when evidence is missing; never infer success from changed
files alone.

## Related skills

- `agent-handoff`
- `final-report-format`
