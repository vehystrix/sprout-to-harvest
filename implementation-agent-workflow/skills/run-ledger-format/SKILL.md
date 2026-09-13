---
name: run-ledger-format
description: "Defines the YAML schema for the durable workflow run ledger in .agent-work."
---
# Run Ledger Format

Use this skill whenever the orchestrator creates or reads `.agent-work/<run-id>/run.yaml`.

## Purpose

`run.yaml` is the durable run-level state. It records invocation identity, the current phase, recovery information, and repository evidence. It is machine-readable YAML, not a narrative report.

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
```

Allowed `phase` values are `initialization`, `plan-audit`, `decomposition`, `step-execution`, `final-verification`, `documentation`, and `finalization`. Allowed `status` values are `pending`, `running`, `completed`, `verification-failed`, `interrupted`, `recoverable`, `blocked`, and `abandoned`.

`maximum_retries` is a non-negative integer. `skip_plan_audit` is a boolean. `resume_from` is either an exact next action string or `null`.

## Write and read rules

- Create the file before the first delegation.
- Update it before and after every delegation.
- Write through a temporary YAML file followed by rename.
- Never overwrite a completed result with a new attempt.
- Preserve blockers and resume instructions when the run is recoverable or blocked.
- Validate the stored invocation fields against the current invocation before resuming.
