---
name: requirements-inventory-format
description: Only use when explicitly invoked
# description: "Defines the YAML schema for the persisted requirements inventory."
user-invocable: false
disable-model-invocation: true
---

The single canonical list of requirements extracted from an implementation plan.

## Purpose

- Persist every material requirement exactly once, with a stable ID and a verbatim
  excerpt, so downstream roles resolve references instead of re-deriving content.
- Provide the source that `requirements_assigned` values in `chunk-index.yaml` resolve against.
- Give the Whole-Plan Verifier the exact plan text against which it checks fidelity.

## Schema (frontmatter-free YAML file)

```yaml
schema: requirements-inventory/v1
run_id: run-001
source: plan-auditor
created_at: 2026-09-29T12:00:00Z
requirements:
  - id: REQ-001
    name: Loader blocks on a missing manifest
    excerpt: |
      When the manifest is missing, the loader returns BLOCKED and names
      the path.
```

### Field rules

- `schema`: literal `requirements-inventory/v1`.
- `run_id`: matches the run directory; unique per run.
- `source`: either `plan-auditor`, when the Plan Auditor derived and wrote the
  file itself, or `plan-decomposer`, when no upstream inventory exists and the
  Plan Decomposer derived and wrote the file.
- `created_at`: ISO 8601 timestamp of persistence.
- `requirements`: non-empty list; every entry carries `id`, `name`, and `excerpt`.

### Entry rules

- `id` is unique across the file, non-empty, and stable for the run's lifetime.
- `name` is a short, stable label for the requirement.
- `excerpt` is verbatim plan text: the exact source passage the requirement was derived
  from, or taken from when the plan lists it explicitly. It must support the requirement
  on its own.

## Cross-cutting requirements

A requirement that spans more than one chunk is split at inventory creation into
sub-requirements, each with its own ID of the form `<parent-id><suffix>` (for example
`REQ-001a`) and its own excerpt.

## Validation

Every consumer that resolves `requirements_assigned` values validates:

- IDs are unique across the file;
- every entry's `id`, `name`, and `excerpt` fields are non-empty.

