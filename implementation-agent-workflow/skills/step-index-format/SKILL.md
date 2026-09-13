---
name: step-index-format
description: "Defines the YAML schema for the dependency-aware implementation step index."
---
# Step Index Format

Use this skill whenever the decomposer writes or an agent reads `.agent-work/<run-id>/step-index.yaml`.

## Schema

```yaml
schema: step-index/v1
run_id: run-001
steps:
  - id: step-001-tests
    type: primary-test
    context_file: steps/step-001-tests.md
    status_file: steps/step-001-tests-status.yaml
    dependencies: []
    status: pending
  - id: step-001-implementation
    type: implementation
    context_file: steps/step-001-implementation.md
    status_file: steps/step-001-implementation-status.yaml
    dependencies:
      - step-001-tests
    status: pending
dependency_order:
  - step-001-tests
  - step-001-implementation
```

Each step ID is unique and appears exactly once. `type` is `primary-test`, `implementation`, or `non-behavioral`. Paths are relative to the run directory. Dependencies must name existing steps and form an acyclic graph. `dependency_order` lists every step exactly once, with each dependency before its dependent.

## Validation

Validate that every step has a Markdown context file, a YAML status-file path, a status, and at least one context requirement, acceptance criterion, and validation command. A behavioral unit must have its primary-test step immediately before its implementation step.
