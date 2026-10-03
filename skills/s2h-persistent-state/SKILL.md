---
name: s2h-persistent-state
description: Only use when explicitly invoked
# description: "Use when coordinating multi-agent implementation work
#   that must survive interruption, cancellation, connection loss, or
#   process failure."
user-invocable: false
disable-model-invocation: true
---
# Persistent Workflow State

Use `s2h-handoff` for every subagent result. Use
`s2h-run-ledger-format`, `s2h-step-status-format`,
`s2h-checkpoint-format`, `s2h-plan-audit-format`,
`s2h-chunk-index-format`, `s2h-requirements-format`,
`s2h-step-context-format`, `s2h-doc-assignment-format`, and
`s2h-final-report-format` for the corresponding persisted files.
Validate each format before copying its status, evidence,
artifacts, blockers, or resume point into the run ledger; an
invalid artifact is `blocked`.

Keep a durable run ledger in an untracked `.agent-work/<run-id>/` directory.

## Artifact format index

The dedicated format skills are the canonical schemas and templates.
This skill only maps each runtime artifact to its format skill
and persistence behavior.

Every file persisted under `.agent-work/<run-id>/` must use one of
these explicit formats and filename patterns:

| Artifact | Filename pattern | Format skill |
| --- | --- | --- |
| Run ledger | `run.json` | `s2h-run-ledger-format` |
| Plan audit | `s2h-plan-audit.json` | `s2h-plan-audit-format` |
| Documentation context | `documentation/source-doc-context.md` and `documentation/user-doc-context.md` | `s2h-doc-context-format` |
| Chunk index | `chunk-index.json` | `s2h-chunk-index-format` |
| Requirement inventory | `requirements.json` | `s2h-requirements-format` |
| Step context | `steps/<step-id>.md` | `s2h-step-context-format` |
| Step status | `steps/<step-id>-status.json` | `s2h-step-status-format` |
| Checkpoint | `checkpoints/<step-id>.json` | `s2h-checkpoint-format` |
| Handoff report | `reports/<phase>-<subject>-<attempt>.json` | `s2h-handoff` |
| Documentation assignment | `documentation/<assignment-id>.md` | `s2h-doc-assignment-format` |
| Final report | `final-report.json` | `s2h-final-report-format` |

No extensionless, YAML, or ad hoc text artifacts are permitted.
Markdown frontmatter must identify the artifact kind,
schema version, ID, and run ID; the body headings must match the
required content for that artifact. JSON state and reports must be
written atomically through a temporary file followed by rename.
Temporary files are implementation details and must not be reported
as artifacts.

The machine-readable artifact schemas are defined by the dedicated
format skills above. Do not copy schemas from this index into other
skills; read the named format skill before creating or validating
that artifact.

Record before and after every subagent:

- phase, step, attempt, assigned agent, and status
- branch and last known commit
- changed files and validation commands
- timestamps, blockers, and resume instructions

Use explicit states: `pending`, `running`, `completed`,
`verification-failed`, `interrupted`, `recoverable`, `blocked`,
and `abandoned`. `completed` is legal only after a verifier returns
`VERIFIED`; an agent's `PASS` does not complete a behavioral step.
`abandoned` marks a user-directed termination set only by the orchestrator;
resuming an `abandoned` run requires an explicit user instruction.
The step-status file is the authoritative record of step progress:
`chunk-index.json` step statuses and the ledger mirror it at transitions, and
on divergence the step-status file wins with a recorded warning.

Write status atomically through a temporary file followed by rename.
On restart, inspect the ledger and the step-status files, and resume the first
`running`, `recoverable`, or `verification-failed` step; otherwise start the
first `pending` step whose dependencies are completed. Never repeat
a verified step unless the user explicitly requests it. Preserve
recoverable workspace changes and report blockers to the user.

Never commit the run directory. Add it to `.git/info/exclude` when appropriate.

## Related skills

- `s2h-handoff`
- `s2h-checkpoint-format`
- `s2h-doc-assignment-format`
- `s2h-doc-context-format`
- `s2h-final-report-format`
- `s2h-chunk-index-format`
- `s2h-plan-audit-format`
- `s2h-requirements-format`
- `s2h-run-ledger-format`
- `s2h-step-context-format`
- `s2h-step-status-format`
