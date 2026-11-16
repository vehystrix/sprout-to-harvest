---
name: s2h-plan-audit
description: "Audit a plan for contradictions, missing interfaces, and unverifiable outcomes."
user-invocable: true
disable-model-invocation: true
---
# Plan Audit

Check each defect class in the plan, recording a finding for every hit:

- Contradictions - statements that cannot all hold at once.
- Impossible requirements - outcomes no implementation can produce.
- Undefined external interfaces - consumed names, signatures, values, or
  sources the plan never defines.
- Missing dependencies - prerequisites with no owner or order in the plan.
- Unnecessary complexity - work duplicating already covered behavior.
- Absent acceptance criteria - requirements with no observable outcome.
- Unverifiable outcomes - results no command, test, or inspection can exercise.

Each finding needs severity, affected requirement(s), consequence, and the
smallest clarification or correction needed; do not silently redesign the plan.

Return one result:

- `BLOCKED` when the plan is impossible, unsafe as written, unreadable enough to
audit, or requires a user decision before decomposition; name each question in
`details.required_questions` and what it would unblock. No implementation work
starts on assumption.
- `DONE` when the plan is specific enough to decompose without inventing
requirements. That does not mean feasible in the current repository: record
repository-dependent risks under findings and validation gaps instead of
guessing at feasibility.

## Documentation context validation

On a `DONE` audit you have written both documentation context files under
`.agent-work/<run-id>/documentation/` per `s2h-doc-context-format`. Before the
DONE handoff, MUST run that skill's validator on both files:

    python3 skills/s2h-doc-context-format/scripts/validate.py <file> [files...]

Fix every named finding internally and re-run until both pass; you wrote both
files, so repair belongs to you. If a finding is unresolvable, return `BLOCKED`
naming the file.

## Related skills

- `s2h-compaction-recovery`: MUST invoke at session start and re-read after every compaction.
