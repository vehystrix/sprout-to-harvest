---
name: plan-audit
description: "Use when reviewing a design specification or implementation
  plan before work begins and ambiguity, feasibility, interface, or scope
  risks may block execution."
---
# Plan Audit

Check for contradictions, impossible requirements, undefined external
interfaces, missing dependencies, unnecessary complexity, absent
acceptance criteria, and unverifiable outcomes.

Return `PASS`, `NEEDS_CLARIFICATION`, or `BLOCKED`. Record each finding with
severity, affected requirement, consequence, and the smallest clarification
or correction needed. Do not silently redesign the plan.
