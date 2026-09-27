---
name: plan-decomposition
description: "Use when splitting an approved implementation plan into small, ordered work units."
---
# Plan Decomposition

Create steps with one clear objective, explicit dependencies, bounded file scope,
required context, acceptance criteria, validation commands, and exclusions.
Use `step-context-format` for each Markdown context file
and `step-index-format` for the dependency index.

Behavioral units must become a primary failing-test step followed by an implementation step.
Keep step files self-contained and preserve requirement IDs so later
verification can trace coverage.
