---
name: step-status-format
description: "Defines the YAML schema for per-step durable execution status."
---
# Step Status Format

Use this skill when the orchestrator creates or reads `steps/<step-id>-status.yaml`.

## Schema

```yaml
schema: step-status/v1
run_id: run-001
step_id: step-001-implementation
phase: step-execution
status: running
attempt: 1
assigned_agent: Step Implementer
repository:
  branch: implementation/run-001
  last_commit: abc1234
  worktree: CHANGED
changed_files: []
validation: []
timestamps:
  started: 2026-09-13T12:05:00Z
  updated: 2026-09-13T12:05:00Z
blockers: []
resume_from: null
```

Allowed statuses are `pending`, `running`, `completed`, `verification-failed`, `interrupted`, `recoverable`, `blocked`, and `abandoned`. `completed` is legal only after a verifier returns `VERIFIED`; an implementer `PASS` is not sufficient.

## Rules

Write this file atomically before and after each delegated call. Preserve attempt counts and evidence across retries. `changed_files` contains repository-relative paths. `validation` contains exact commands, results, and evidence. A blocked or recoverable status must provide `resume_from`.
