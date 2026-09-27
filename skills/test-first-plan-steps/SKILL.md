---
name: test-first-plan-steps
description: >-
  Use when decomposing a behavioral implementation plan into independently
  executable test-driven steps.
---
# Test-First Plan Steps

Split every behavioral unit into ordered steps:

1. **Primary tests:** define the external behavior, write focused failing
   tests, and prove they fail for the intended reason.
2. **Implementation:** read the test-step context, implement the minimum
   behavior, and make the primary tests pass.

The implementation step may add supplementary tests only for discovered edge
cases or regressions. It must not replace or silently rewrite the primary
tests.

Each step records requirements, dependencies, interfaces, files, acceptance
criteria, validation commands, expected state, exclusions, and commit
expectations using `step-context-format`. Mark purely mechanical or
infrastructure work `non-behavioral` with a reason when a failing test is not
meaningful.
