---
name: plan-decomposition
description: "Use when splitting an approved implementation plan into small, ordered work units."
user-invocable: true
disable-model-invocation: true
---
# Plan Decomposition

When invoked directly by the user outside an orchestrated run, produce no
persisted workflow artifacts (`agent-handoff` reports or `.agent-work/` state);
report results conversationally instead. When delegated from the orchestrator
or a role agent, persist outputs exactly as this skill and its format skills describe.

Decompose the approved plan into steps with one clear objective each, explicit
dependencies, bounded file scope, required context, acceptance criteria,
validation commands, and exclusions. Keep step files self-contained and preserve
requirement IDs so later verification can trace coverage.
Record a task complexity note for each step covering its required capabilities and complexity.
Use `step-context-format` for each Markdown step context file.

For behavioral units, follow `test-first-plan-steps`: a primary failing-test
step followed by an implementation step. Mark infrastructure or purely
mechanical work `non-behavioral` with a reason when no failing test is meaningful.

Stop with a blocked result if any dependency cycle, unassigned requirement,
missing acceptance criterion, or missing validation command remains.

## Related skills

- `step-context-format`
- `test-first-plan-steps`
