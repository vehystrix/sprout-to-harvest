---
name: s2h-subagent-recovery
description: Only use when explicitly invoked
# description: "Use when a delegated agent is interrupted, cancelled, loses its
#   connection, encounters unavailable resources, or cannot complete because of
#   permissions or another unrecoverable error."
user-invocable: false
disable-model-invocation: true
---
# Subagent Recovery

Record recovery through `s2h-handoff` with `status: RECOVERABLE`, and persist
the durable checkpoint using `s2h-checkpoint-format` and step state using
`s2h-step-status-format`. Include the last known artifacts and repository state, the
blocker, and an exact `resume_from` action.

Distinguish interruption from implementation failure.

On interruption or blockage:

1. Persist `interrupted`, `recoverable`, or `blocked` status.
2. Record the error category, last checkpoint, branch, commit, changed files, and workspace safety.
3. Preserve the workspace; never restart the whole run or discard edits.
4. Report the blocker and required user action.
5. Resume the same step from its checkpoint after the issue is resolved.

A completed and verified step is never rerun automatically; resume a partially
completed step from its checkpoint per `s2h-checkpoint-format`. Ordinary verification
failures follow the per-step retry cap recorded in `run.json` by
`s2h-orchestrator`; at the cap, stop with `BLOCKED` (escalation is
disabled by policy default).

## Related skills

- `s2h-handoff`
- `s2h-checkpoint-format`
- `s2h-step-status-format`
