---
name: chunk-index-format
description: Only use when explicitly invoked
# description: "Defines the YAML schema for the decomposition chunk index."
user-invocable: false
disable-model-invocation: true
---

The machine-readable ownership map of a decomposed implementation plan.

## Purpose

- Record one entry per chunk with its assigned requirement IDs,
  documentation-loop status, and step list.
- Persist model recommendations and assignments for the four roles the pipeline delegates to.
- Keep contracts out of the index: they live verbatim in each chunk's step files,
  shaped by `step-context-format`, and every `requirements_assigned` ID resolves into
  `requirements-inventory.yaml`.

## Schema (frontmatter-free YAML file)

```yaml
schema: chunk-index/v1
run_id: run-001
chunks:
  - id: chunk-001
    kind: behavioral
    requirements_assigned: [REQ-001]
    doc_status: pending
    steps:
      - id: step-001-tests
        type: primary-test
        context_file: steps/step-001-tests.md
        status_file: steps/step-001-tests-status.yaml
        dependencies: []
        status: pending
      - id: step-002-implementation
        type: implementation
        context_file: steps/step-002-implementation.md
        status_file: steps/step-002-implementation-status.yaml
        dependencies: [step-001-tests]
        status: pending
    model_recommendations:
      chunk-writer:
        portable_id: fast
        rationale: Bounded single-chunk doc loop; no long-horizon reasoning needed.
        required_capabilities: [read, search, edit]
        complexity: low
      chunk-verifier:
        portable_id: standard
        rationale: Intra-chunk completeness check against fixed contract excerpts.
        required_capabilities: [read, search]
        complexity: moderate
      implementer:
        portable_id: null
        rationale: Not final; the orchestrator persists this assignment at step selection.
        required_capabilities: []
        complexity: unknown
      verifier:
        portable_id: standard
        rationale: Implementation verification within one step's scope.
        required_capabilities: [read, search]
        complexity: moderate
    model_assignments:
      chunk-writer:
        portable_id: fast
        assigned_at: 2026-09-29T12:05:00Z
        source: decomposer
      chunk-verifier:
        portable_id: standard
        assigned_at: 2026-09-29T12:05:00Z
        source: decomposer
```

The `chunks` list is the top level of the file; every run's decomposition state lives
under it. Each step ID in the file is unique and appears exactly once. A chunk's `kind`
is either `behavioral`, which carries exactly two steps - a `primary-test` step
immediately before its dependent `implementation` step, with the implementation listing
the test in `dependencies` - or `non-behavioral`, which carries exactly one step of type
`non-behavioral`. File paths are relative to the run directory.

`requirements_assigned` carries requirement IDs only: no excerpts, interfaces, end-state
descriptions, or exclusion lists. Each ID must resolve into the run's
`requirements-inventory.yaml`, and each inventory requirement appears in exactly one
chunk's list; that coverage check runs when the decomposer writes the index and again,
independently, in the Whole-Plan Verifier pass.

`doc_status` is a per-chunk value: `pending`, `running`, `verification-failed`, or
`completed`. The Plan Decomposer initializes it to `pending` when it writes the index,
persists `running` before each writer delegation, persists `verification-failed` after an
`INCOMPLETE` verdict, and sets `completed` only after a `VERIFIED` verdict.

`model_recommendations` is optional and records the decomposer's non-final guidance for all
four roles - `chunk-writer`, `chunk-verifier`, `implementer`, `verifier`. Each role entry
carries `portable_id`, `rationale`, `required_capabilities`, and `complexity`, or an
explicit `null` when no recommendation applies. `model_assignments` is required with one
block per the four roles in the shape shown above: the Plan Decomposer persists the
documentation-loop assignments (`chunk-writer`, `chunk-verifier`) when it delegates, and
the orchestrator persists the implementation-loop ones during step selection. The
whole-plan verifier's assignment is recorded only in that delegation's handoff details;
it never appears in the index.

## Validation

Validate structure: every chunk carries an `id`, a `kind`, exactly one allowed
`doc_status` value, and a non-empty `requirements_assigned` list matching its kind -
behavioral chunks with exactly two steps in test-to-implementation order carrying the
dependency edge, non-behavioral chunks with exactly one step. Validate that step IDs are
unique file-wide, dependencies form an acyclic graph naming only existing steps, and
every model block is complete for all four roles.

The orchestrator runs this final structural validation on the finished index. The Step
Decomposer checks the same invariants before it returns, and routes its own repairs
first: a failed check is fixed by the decomposer re-delegating or rewriting, not
escalated to the orchestrator as an infrastructure failure.
