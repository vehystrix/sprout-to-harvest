---
name: plan-audit
description: "Audit a plan for contradictions, missing interfaces, and unverifiable outcomes."
user-invocable: true
disable-model-invocation: true
---
# Plan Audit

When invoked directly by the user outside an orchestrated run, produce no
persisted workflow artifacts (`agent-handoff` reports or `.agent-work/` state);
report results conversationally instead. When delegated from the orchestrator
or a role agent, persist outputs exactly as this skill and its format skills describe.

Check for contradictions, impossible requirements, undefined external
interfaces, missing dependencies, unnecessary complexity, absent
acceptance criteria, and unverifiable outcomes.

Return `PASS`, `NEEDS_CLARIFICATION`, or `BLOCKED`. Record each finding with
severity, affected requirement, consequence, and the smallest clarification
or correction needed. Do not silently redesign the plan.
