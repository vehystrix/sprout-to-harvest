---
name: plan-audit
description: Only use when explicitly invoked
# description: "Use when reviewing a design specification or implementation
#   plan before work begins and ambiguity, feasibility, interface, or scope
#   risks may block execution."
user-invocable: false
disable-model-invocation: true
---
# Plan Audit

Check for contradictions, impossible requirements, undefined external
interfaces, missing dependencies, unnecessary complexity, absent
acceptance criteria, and unverifiable outcomes.

Return `PASS`, `NEEDS_CLARIFICATION`, or `BLOCKED`. Record each finding with
severity, affected requirement, consequence, and the smallest clarification
or correction needed. Do not silently redesign the plan.
