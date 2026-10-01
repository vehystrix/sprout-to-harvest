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

- `BLOCKED` when the plan is impossible, unsafe as written, or unreadable enough to audit.
- `NEEDS_CLARIFICATION` when implementation could proceed only after a user decision;
  name each question and what it would unblock.
- `PASS` when the plan is specific enough to decompose without inventing requirements.
  That does not mean feasible in the current repository: record repository-dependent
  risks under findings and validation gaps instead of guessing at feasibility.
