---
name: subagent-recovery
description: Only use when explicitly invoked
# description: "Use when a delegated agent is interrupted, cancelled, loses its
#   connection, encounters unavailable resources, or cannot complete because of
#   permissions or another unrecoverable error."
user-invocable: false
disable-model-invocation: true
---
# Subagent Recovery

Record recovery through `agent-handoff` with `status: RECOVERABLE`, and persist
the durable checkpoint using `checkpoint-format` and step state using
`step-status-format`. Include the last known artifacts and repository state, the
blocker, and an exact `resume_from` action.

Distinguish interruption from implementation failure.

On interruption or blockage:

1. Persist `interrupted`, `recoverable`, or `blocked` status.
2. Record the error category, last checkpoint, branch, commit, changed files, and workspace safety.
3. Preserve the workspace; never restart the whole run or discard edits.
4. Report the blocker and required user action.
5. Resume the same step from its checkpoint after the issue is resolved.

A completed and verified step is never rerun automatically. A partially
completed step is resumed using its context file and latest report. Use a
finite retry limit for ordinary verification failures; escalate after the
limit.

## Related skills

- `agent-handoff`
- `checkpoint-format`
- `step-status-format`
