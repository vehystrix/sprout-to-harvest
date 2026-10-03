---
name: s2h-chunk-index-format
description: Only use when explicitly invoked
# description: "Defines the JSON schema for the decomposition chunk index."
user-invocable: false
disable-model-invocation: true
---

The machine-readable ownership map of a decomposed implementation plan.

## Purpose

- Record one entry per chunk with its assigned requirement IDs,
  documentation-loop status, and step list.
- Persist model recommendations and assignments for the four roles the pipeline delegates to.
- Keep contracts out of the index: they live verbatim in each chunk's step files,
  shaped by `s2h-step-context-format`, and every `requirements_assigned` ID resolves into
  `requirements.json`.

## Schema (frontmatter-free JSON file)

```json
{
  "schema": "s2h-chunk-index/v1",
  "run_id": "run-001",
  "chunks": [
    {
      "id": "chunk-001",
      "kind": "behavioral",
      "requirements_assigned": ["REQ-001"],
      "doc_status": "pending",
      "steps": [
        {
          "id": "step-001-tests",
          "type": "primary-test",
          "context_file": "steps/step-001-tests.md",
          "status_file": "steps/step-001-tests-status.json",
          "dependencies": [],
          "status": "pending"
        },
        {
          "id": "step-002-implementation",
          "type": "implementation",
          "context_file": "steps/step-002-implementation.md",
          "status_file": "steps/step-002-implementation-status.json",
          "dependencies": ["step-001-tests"],
          "status": "pending"
        }
      ],
      "model_recommendations": {
        "chunk-writer": {
          "portable_id": "fast",
          "rationale": "Bounded single-chunk doc loop; no long-horizon reasoning needed.",
          "required_capabilities": ["read", "search", "edit"],
          "complexity": "low"
        },
        "chunk-verifier": {
          "portable_id": "standard",
          "rationale": "Intra-chunk completeness check against fixed contract excerpts.",
          "required_capabilities": ["read", "search"],
          "complexity": "moderate"
        },
        "implementer": {
          "portable_id": null,
          "rationale": "Not final; the orchestrator persists this assignment at step selection.",
          "required_capabilities": [],
          "complexity": "unknown"
        },
        "verifier": {
          "portable_id": "standard",
          "rationale": "Implementation verification within one step's scope.",
          "required_capabilities": ["read", "search"],
          "complexity": "moderate"
        }
      },
      "model_assignments": {
        "chunk-writer": {
          "portable_id": "fast",
          "assigned_at": "2026-09-29T12:05:00Z",
          "source": "decomposer"
        },
        "chunk-verifier": {
          "portable_id": "standard",
          "assigned_at": "2026-09-29T12:05:00Z",
          "source": "decomposer"
        }
      }
    }
  ]
}
```

The `chunks` list is the top level of the file; every run's decomposition state lives
under it. File paths are relative to the run directory.

`requirements_assigned` carries requirement IDs only: no excerpts, interfaces, end-state
descriptions, or exclusion lists. Each ID must resolve into the run's
`requirements.json`.

The machine-readable form is defined by `references/schema.json`; validate a file with
`scripts/validate.py <file>`.
`doc_status` is a per-chunk value: `pending`, `running`, `verification-failed`, or `completed`.

`model_recommendations` is optional and records the `s2h-PlanDecomposer`'s non-final guidance for
all four roles - `chunk-writer`, `chunk-verifier`, `implementer`, `verifier`; each role entry
carries `portable_id`, `rationale`, `required_capabilities`, and `complexity`, or an
explicit `null`. `model_assignments` is required with one block per the four roles in the
shape shown above. The `s2h-WholePlanVerifier`'s assignment is recorded only in that delegation's
handoff details; it never appears in the index.

## Validation

Validate structure: every chunk carries an `id`, a `kind`, exactly one allowed
`doc_status` value, and a non-empty `requirements_assigned` list matching its kind -
behavioral chunks with exactly two steps in test-to-implementation order carrying the
dependency edge, non-behavioral chunks with exactly one step. Validate that step IDs are
unique file-wide, dependencies form an acyclic graph naming only existing steps, and
every model block is complete for all four roles.

