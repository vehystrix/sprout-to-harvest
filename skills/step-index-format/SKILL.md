---
name: step-index-format
description: Only use when explicitly invoked
# description: "Defines the YAML schema for the dependency-aware implementation step index."
user-invocable: false
disable-model-invocation: true
---
# Step Index Format

Use this skill whenever the decomposer writes `.agent-work/<run-id>/step-index.yaml`,
and whenever the orchestrator validates it or persists per-chunk documentation status.

## Schema

```yaml
schema: step-index/v1
run_id: run-001
steps:
  - id: step-001-tests
    type: primary-test
    chunk_id: chunk-001
    doc_status: pending
    context_file: steps/step-001-tests.md
    status_file: steps/step-001-tests-status.yaml
    dependencies: []
    status: pending
    contract:
      requirements_assigned: [REQ-001]
      requirement_excerpts:
        REQ-001: |
          When the manifest is missing, the loader returns BLOCKED and names
          the path.
      interfaces_in: []
      interfaces_out:
        - name: load_manifest
          signature: "load_manifest(path) -> Manifest"
      end_state: A failing primary test proves the loader detects a missing manifest.
      exclusions: [production loader changes]
    model_recommendations:
      doc_writer:
        portable_id: reasoning-pro
        rationale: "Fleshes out this chunk's step documentation."
        required_capabilities: [planning, reasoning]
        complexity: medium
      doc_verifier:
        portable_id: reasoning-pro
        rationale: "Independent verification of requirement coverage."
        required_capabilities: [verification, reasoning]
        complexity: high
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
      doc_writer:
        portable_id: reasoning-pro
        requested: reasoning-pro
        resolved: Claude Sonnet 4.5 (copilot)
        source: orchestrator
        fallback: null
        applied: true
        adapter: copilot
        evidence: adapter-confirmed
        runtime_model: Claude Sonnet 4.5 (copilot)
        warning: null
      doc_verifier:
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
    chunk_id: chunk-001
    doc_status: pending
    context_file: steps/step-001-implementation.md
    status_file: steps/step-001-implementation-status.yaml
    dependencies:
      - step-001-tests
    status: pending
    contract:
      requirements_assigned: [REQ-001]
      requirement_excerpts:
        REQ-001: |
          When the manifest is missing, the loader returns BLOCKED and names
          the path.
      interfaces_in:
        - name: failing primary test for load_manifest
      interfaces_out:
        - name: load_manifest
          signature: "load_manifest(path) -> Manifest"
      end_state: The primary tests pass against a loader that detects a missing manifest.
      exclusions: [loader changes beyond REQ-001]
    model_recommendations:
      doc_writer:
        portable_id: reasoning-pro
        rationale: "Fleshes out this chunk's step documentation."
        required_capabilities: [planning, reasoning]
        complexity: medium
      doc_verifier:
        portable_id: reasoning-pro
        rationale: "Independent verification of requirement coverage."
        required_capabilities: [verification, reasoning]
        complexity: high
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
      doc_writer:
        portable_id: reasoning-pro
        requested: reasoning-pro
        resolved: Claude Sonnet 4.5 (copilot)
        source: orchestrator
        fallback: null
        applied: true
        adapter: copilot
        evidence: adapter-confirmed
        runtime_model: Claude Sonnet 4.5 (copilot)
        warning: null
      doc_verifier:
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

Each step ID is unique and appears exactly once. `type` is
`primary-test`, `implementation`, or `non-behavioral`. Paths are
relative to the run directory. Dependencies must name existing steps
and form an acyclic graph. `dependency_order` lists every step
exactly once, with each dependency before its dependent.

Every step carries a `chunk_id` naming its decomposition chunk and a
`doc_status` value (`pending`, `running`, `verification-failed`, or
`completed`). The decomposer initializes `doc_status` to `pending`; the
orchestrator persists it during the documentation loop: `running` before
each writer delegation, `verification-failed` after an `INCOMPLETE`, and
`completed` only after a `VERIFIED`. All steps sharing one `chunk_id`
carry verbatim-identical `contract` blocks and identical `doc_status`
values.

The `contract` block is the chunk contract: `requirements_assigned` lists
the requirement IDs this chunk owns, `requirement_excerpts` carries the
verbatim plan text for each assigned ID, `interfaces_in` and
`interfaces_out` name what the chunk consumes from or produces for other
chunks (produced interfaces use `name` plus `signature`), `end_state`
describes in one paragraph what exists when the chunk completes, and `exclusions` lists work the
chunk must not do. These are the same fields
embedded verbatim in every step file of the chunk under its `Contract`
heading per `step-context-format`.

`model_recommendations` is optional and records the decomposer's
non-final guidance for the documentation loop roles (`doc_writer`,
`doc_verifier`) as well as the implementation loop roles (`implementer`,
`verifier`). Each role entry carries a `portable_id`, `rationale`,
`required_capabilities`, and `complexity`; each role is present or an
explicit `null`. `model_assignments` is required for orchestrator-resolved
runtime assignments and must contain one block per the four roles, in the
shape shown above. The original recommendation remains auditable in the
step index, while the final resolved assignment is the operational value
used for delegation. Documentation model selection is not part of the step
decomposition contract.

## Validation

Validate that every step has a `chunk_id`, an allowed `doc_status`, and a
complete `contract` block; all steps sharing one `chunk_id` carry
verbatim-identical contract blocks and identical `doc_status`.
Validate that every step names a Markdown context-file path, a YAML
status-file path, a status, and at least one requirement, acceptance
criterion, and validation command in its declared scope; the existence of
each `context_file` is checked after the Step Documentation Writer
produces it, not when the decomposer writes the index. A behavioral unit
must have its primary-test step immediately before its implementation step
within its chunk. Validate that each step records either a
`model_recommendations` block or an explicit `null` explanation, and that
each step has a `model_assignments` section with normalized `portable_id`,
`source`, `applied`, `adapter`, and `evidence` values for all four roles.
