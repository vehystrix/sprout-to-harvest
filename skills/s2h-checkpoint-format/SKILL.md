---
name: s2h-checkpoint-format
description: Only use when explicitly invoked
# description: "Defines the JSON schema for resumable step checkpoints."
user-invocable: false
disable-model-invocation: true
---
# Checkpoint Format

Use this skill when an implementer records or resumes `checkpoints/<step-id>.json`.

## Schema

```json
{
  "schema": "s2h-checkpoint/v1",
  "run_id": "run-001",
  "step_id": "step-001-implementation",
  "status": "recoverable",
  "last_completed_action": "Focused tests pass; commit is pending.",
  "changed_files": ["src/example.ts"],
  "validation": [
    {
      "command": "npm test -- example.test.ts",
      "result": "PASS",
      "evidence": "3 tests passed."
    }
  ],
  "repository": {
    "branch": "implementation/run-001",
    "last_commit": "abc1234",
    "worktree": "CHANGED"
  },
  "timestamp": "2026-09-13T12:10:00Z",
  "blockers": [
    {
      "id": "COMMIT_UNAVAILABLE",
      "reason": "Git credentials are unavailable."
    }
  ],
  "resume_from": "Commit the validated changes on the implementation branch."
}
```

The machine-readable form is defined by `references/schema.json`; validate a file with
`scripts/validate.py <file>`.

`last_completed_action` is a factual milestone, not a plan. Include
enough changed-file, validation, and repository evidence for another
agent to resume safely. Use `status: completed` only for a finished
checkpoint; use `recoverable`, `interrupted`, or `blocked` when work
needs attention.
