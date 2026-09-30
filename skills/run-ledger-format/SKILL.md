---
name: run-ledger-format
description: Only use when explicitly invoked
# description: "Defines the YAML schema for the durable workflow run ledger in .agent-work."
user-invocable: false
disable-model-invocation: true
---
# Run Ledger Format

Use this skill whenever the orchestrator creates `.agent-work/<run-id>/run.yaml`.

## Purpose

`run.yaml` is the durable run-level state. It records invocation identity, the current phase,
recovery information, and repository evidence. It is machine-readable YAML, not a
narrative report.

## Schema

Required top-level fields:

```yaml
schema: workflow-run/v1
run_id: run-001
plan: path/to/plan.md
run_directory: .agent-work/run-001
maximum_retries: 2
skip_plan_audit: false
phase: initialization
status: pending
attempt: 0
repository:
  branch: N/A
  last_commit: N/A
  worktree: UNKNOWN
  tracked_changes: []
timestamps:
  created: 2026-09-13T12:00:00Z
  updated: 2026-09-13T12:00:00Z
validation: []
blockers: []
resume_from: null
model_routing:
  catalog_source: .implementation-agent/model-catalog.yaml
  policy_source: .implementation-agent/model-policy.yaml
  adapter: copilot                # active host identifier (the hosts.<...> key used)
  preflight:
    status: passed               # or routing-unavailable when no honored selector exists
    mechanism: model-parameter   # or none
    evidence_channel: tool-reported  # or self-reported
  catalog_fingerprint: sha256:8df8d9b3d56642551d7b230c7f1f7499a2d7e7d818e94755aef57b6c1be2db3d
  policy_fingerprint: sha256:3c3d22b13a901d43e9d1f9b2f7d66f0d7a89c8b0f0b9f8d3972189a4408d68c
  override_confirmed: false
  warnings: []
```

Allowed `phase` values are `initialization`, `plan-audit`, `decomposition`,
`step-execution`, `final-verification`, `documentation`, and `finalization`.
Allowed `status` values are `pending`, `running`, `completed`,
`verification-failed`, `interrupted`, `recoverable`, `blocked`, and
`abandoned`.

`maximum_retries` is a non-negative integer. `skip_plan_audit` is a boolean.
`resume_from` is either an exact next action string or `null`.

The `model_routing` block is required whenever dynamic routing is enabled. It records
the effective catalog and policy source files, the active host identifier, and the
one-time capability probe result: `catalog_source` and `policy_source` identify the YAML
configuration files used for this run; `adapter` is the active host identifier - the value
appearing under `hosts.*` in the catalog - not a compiled module; and the `preflight`
block records the capability probe result (`status`, `mechanism`, `evidence_channel`). It also
holds the canonicalized fingerprints of the confirmed configuration, whether an invocation
override was explicitly confirmed, and any persisted warning values.

A missing or malformed `model_routing` block is `BLOCKED` before delegated
implementation work. Fingerprints are canonical SHA-256 values per
`model-catalog-format`; they serve as resume, override-review, and audit evidence.
Resumed runs reuse the copied run-level files when present and compare their
fingerprints against the current repository configuration before continuing.
