---
name: run-ledger-format
description: "Defines the YAML schema for the durable workflow run ledger in .agent-work."
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

The `model_routing` block is required whenever dynamic routing is enabled. It
records the effective catalog and policy source files, the active host identifier,
and the one-time capability probe result. `catalog_source` and `policy_source` identify
the YAML configuration files used for this run; `adapter` is the active host
identifier - the value appearing under `hosts.*` in the catalog - not a compiled
module; and the `preflight` block records the capability probe result: whether a
per-delegation selector was confirmed (`status`), which mechanism exposes it
(`mechanism`), and which evidence channel applies (`evidence_channel`). It also holds
the canonicalized fingerprints of the confirmed configuration, whether an invocation
override was explicitly confirmed, and any persisted warning values. Resumed runs must
reuse the copied run-level files when they exist and compare them against the current
repository configuration before continuing.

## Write and read rules

- Create the file before the first delegation.
- Update it before and after every delegation.
- Write through a temporary YAML file followed by rename.
- Never overwrite a completed result with a new attempt.
- Preserve blockers and resume instructions when the run is recoverable or blocked.
- Validate the stored invocation fields against the current invocation before resuming.
- Before any delegated work begins, copy the effective model catalog and policy under
`.agent-work/<run-id>/` and persist the corresponding `model_routing` block. The run copies are
the authoritative runtime inputs for that attempt; resumed runs reuse those copied files
and compare their fingerprints to the current repository values before delegation.
- Run the capability probe exactly once per run using the model-routing-adapter procedure and
persist its result in `model_routing.preflight` along with the active host identifier, the
confirmed fingerprints, and any warnings. Reusing a cached probe result is valid only while
the same host, session, and effective configuration fingerprint are still in use; otherwise
record a warning.
- `catalog_fingerprint` and `policy_fingerprint` must come from the canonical SHA-256
representation of the effective files after merge and validation. The fingerprint is evidence
for resume, override review, and auditability. `override_confirmed` records whether an
explicit override value was accepted for the current run; when false, the override still may be
visible in the stored policy decision but must not masquerade as a silent policy change.
- Persist warnings in `model_routing.warnings` whenever the run chooses a fallback, receives
a host-reported runtime mismatch, or otherwise proceeds in a legacy-compatible mode. Legacy
mode must remain visible in the run ledger so downstream agents can distinguish compatibility
behavior from a normal dynamic assignment.
- A missing or malformed `model_routing` block is `BLOCKED` before the orchestrator delegates
implementation work.
