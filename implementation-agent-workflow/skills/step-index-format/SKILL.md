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
    model_recommendations:
      implementer:
        portable_id: coding-standard
        rationale: "Needs focused test authoring and code changes."
        required_capabilities: [coding, testing]
        complexity: medium
      verifier:
        portable_id: reasoning-pro
        rationale: "Independent verification of the failing assertion."
        required_capabilities: [verification, reasoning]
        complexity: high
    model_assignments:
      implementer:
        portable_id: coding-standard
        requested: coding-standard
        resolved: Code Model (copilot)
        source: orchestrator
        fallback: null
        applied: true
        adapter: copilot
        evidence: adapter-confirmed
        runtime_model: Code Model (copilot)
        warning: null
      verifier:
        portable_id: reasoning-pro
        requested: reasoning-pro
        resolved: Claude Opus 4.8 (copilot)
        source: orchestrator
        fallback: null
        applied: true
        adapter: copilot
        evidence: adapter-confirmed
        runtime_model: Claude Opus 4.8 (copilot)
        warning: null
  - id: step-001-implementation
    type: implementation
    context_file: steps/step-001-implementation.md
    status_file: steps/step-001-implementation-status.yaml
    dependencies:
      - step-001-tests
    status: pending
    model_recommendations:
      implementer:
        portable_id: coding-standard
        rationale: "Keeps the fix scoped to the implementation step."
        required_capabilities: [coding, testing]
        complexity: medium
      verifier:
        portable_id: reasoning-pro
        rationale: "Requires validation against the acceptance criteria."
        required_capabilities: [verification, reasoning]
        complexity: high
    model_assignments:
      implementer:
        portable_id: coding-standard
        requested: coding-standard
        resolved: Code Model (copilot)
        source: orchestrator
        fallback: null
        applied: true
        adapter: copilot
        evidence: adapter-confirmed
        runtime_model: Code Model (copilot)
        warning: null
      verifier:
        portable_id: reasoning-pro
        requested: reasoning-pro
        resolved: Claude Opus 4.8 (copilot)
        source: orchestrator
        fallback: null
        applied: true
        adapter: copilot
        evidence: adapter-confirmed
        runtime_model: Claude Opus 4.8 (copilot)
        warning: null
dependency_order:
  - step-001-tests
  - step-001-implementation
```

Each step ID is unique and appears exactly once. `type` is `primary-test`, `implementation`, or `non-behavioral`. Paths are relative to the run directory. Dependencies must name existing steps and form an acyclic graph. `dependency_order` lists every step exactly once, with each dependency before its dependent.

`model_recommendations` is optional and records the decomposer's non-final guidance. `model_assignments` is required for orchestrator-resolved runtime assignments. The original recommendation remains auditable in the step index, while the final resolved assignment is the operational value used for delegation. Documentation model selection is not part of the step decomposition contract.

## Validation

Validate that every step has a Markdown context file, a YAML status-file path, a status, and at least one context requirement, acceptance criterion, and validation command. A behavioral unit must have its primary-test step immediately before its implementation step. Validate that each step records either a `model_recommendations` block or an explicit `null` explanation, and that each step has a `model_assignments` section with normalized `portable_id`, `source`, `applied`, `adapter`, and `evidence` values for the implementer and verifier roles.
