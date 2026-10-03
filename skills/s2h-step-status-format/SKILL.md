---
name: s2h-step-status-format
description: Only use when explicitly invoked
# description: "Defines the JSON schema for per-step durable execution status."
user-invocable: false
disable-model-invocation: true
---
# Step Status Format

Use this skill when the orchestrator creates `steps/<step-id>-status.json`.

## Schema

```json
{
  "schema": "s2h-step-status/v1",
  "run_id": "run-001",
  "step_id": "step-001-implementation",
  "phase": "step-execution",
  "status": "running",
  "attempt": 1,
  "assigned_agent": "s2h-StepImplementer",
  "repository": {
    "branch": "implementation/run-001",
    "last_commit": "abc1234",
    "worktree": "CHANGED"
  },
  "changed_files": [],
  "validation": [],
  "model_assignment": {
    "requested": "coding-standard",
    "resolved": "Code Model (copilot)",
    "portable_id": "coding-standard",
    "role": "implementer",
    "source": "orchestrator",
    "fallback": null,
    "applied": true,
    "adapter": "copilot",
    "evidence": "adapter-confirmed",
    "runtime_model": "Code Model (copilot)",
    "rationale": "Implementation requires coding and testing support.",
    "warning": null
  },
  "attempt_history": [
    {
      "attempt": 0,
      "assignment": {
        "portable_id": "coding-standard",
        "requested": "coding-standard",
        "resolved": "Code Model (copilot)",
        "source": "decomposer",
        "fallback": null,
        "applied": true,
        "evidence": "adapter-confirmed",
        "runtime_model": "Code Model (copilot)",
        "warning": null
      },
      "outcome": "verified",
      "escalation": {
        "triggered": false,
        "prior_model": null,
        "new_model": null,
        "policy_rule": null
      }
    }
  ],
  "timestamps": {
    "started": "2026-09-13T12:05:00Z",
    "updated": "2026-09-13T12:05:00Z"
  },
  "blockers": [],
  "resume_from": null
}
```

The machine-readable form is defined by `references/schema.json`; validate a file with
`scripts/validate.py <file>`.

Allowed statuses are `pending`, `running`, `completed`,
`verification-failed`, `interrupted`, `recoverable`, `blocked`,
and `abandoned`.
`completed` is legal only after a verifier returns `VERIFIED`; an agent's
`PASS` does not complete a behavioral step.

`model_assignment` is the resolved assignment for the current attempt.
`attempt_history` is append-only, in chronological order; each entry records
the attempt number, the prior assignment snapshot, the documented outcome,
and any escalation metadata: `triggered`, `prior_model`, `new_model`, and `policy_rule`.

## Rules

Write this file atomically before and after each delegated call.
Preserve attempt counts and evidence across retries.
`changed_files` contains repository-relative paths.
`validation` contains exact commands, results, and evidence. A
blocked or recoverable status must provide `resume_from`. The step
status must never silently replace a prior assignment with a new
model when a retry is a preservation move; any policy-authorized
escalation must be explicit and persisted under
`attempt_history[].escalation`.
