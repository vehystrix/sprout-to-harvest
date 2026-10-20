---
name: s2h-verification-before-completion
description: "MUST use before completing a task; verify completion with executable evidence"
user-invocable: true
disable-model-invocation: false
---

# Verification Before Completion

User mode: report conversationally; no `.agent-work` artifacts or `s2h-handoff`
reports. Delegated mode: persist per this skill and its format skills.
Verify only the assigned work; report defects without repairing them during verification.

Return verification results through `s2h-handoff`; persisted reports
must use its JSON schema. A `DONE` status requires fresh executable
evidence for every material requirement in the handoff; missing,
contradictory, or unverifiable evidence - including a deviation no
ground-truth record can settle - is `BLOCKED` naming the exact gap.
Never reinterpret a value or retry automatically. The final plan-level
result must additionally follow `s2h-final-report-format`.

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

- `s2h-handoff`
- `s2h-final-report-format`
