---
name: persistent-workflow-state
description: "Use when coordinating multi-agent implementation work that must survive interruption, cancellation, connection loss, or process failure."
---
# Persistent Workflow State

Use `agent-handoff` for every subagent result. Use `run-ledger-format`, `step-status-format`, `checkpoint-format`, `plan-audit-format`, `step-index-format`, `step-context-format`, `documentation-assignment-format`, and `final-report-format` for the corresponding persisted files. Validate each format before copying its status, evidence, artifacts, blockers, or resume point into the run ledger; an invalid artifact is `blocked`.

Keep a durable run ledger in an untracked `.agent-work/<run-id>/` directory.

## Artifact format index

The dedicated format skills are the canonical schemas and templates. This skill only maps each runtime artifact to its format skill and persistence behavior.

Every file persisted under `.agent-work/<run-id>/` must use one of these explicit formats and filename patterns:

| Artifact | Filename pattern | Format skill |
| --- | --- | --- |
| Run ledger | `run.yaml` | `run-ledger-format` |
| Plan audit | `plan-audit.yaml` | `plan-audit-format` |
| Documentation context | `documentation/source-documentation-context.md` and `documentation/user-documentation-context.md` | `documentation-context-format` |
| Step index | `step-index.yaml` | `step-index-format` |
| Step context | `steps/<step-id>.md` | `step-context-format` |
| Step status | `steps/<step-id>-status.yaml` | `step-status-format` |
| Checkpoint | `checkpoints/<step-id>.yaml` | `checkpoint-format` |
| Handoff report | `reports/<phase>-<subject>-<attempt>.yaml` | `agent-handoff` |
| Documentation assignment | `documentation/<assignment-id>.md` | `documentation-assignment-format` |
| Final report | `final-report.yaml` | `final-report-format` |

Do not create extensionless, JSON, or ad hoc text artifacts in the run directory. Markdown frontmatter must identify the artifact kind, schema version, ID, and run ID; the body headings must match the required content for that artifact. YAML state and reports must be written atomically through a temporary file followed by rename. Temporary files are implementation details and must not be reported as artifacts.

The machine-readable artifact schemas are defined by the dedicated format skills above. Do not copy schemas from this index into other skills; read the named format skill before creating or validating that artifact.


Record before and after every subagent:

- phase, step, attempt, assigned agent, and status
- branch and last known commit
- changed files and validation commands
- timestamps, blockers, and resume instructions

Use explicit states: `pending`, `running`, `completed`, `verification-failed`, `interrupted`, `recoverable`, `blocked`, and `abandoned`. `completed` is legal only after a verifier returns `VERIFIED`; an agent's `PASS` does not complete a behavioral step.

Write status atomically through a temporary file followed by rename. On restart, inspect the ledger and resume the first `running`, `recoverable`, or `verification-failed` step; otherwise start the first `pending` step whose dependencies are completed. Never repeat a verified step unless the user explicitly requests it. Preserve recoverable workspace changes and report blockers to the user.

Never commit the run directory. Add it to `.git/info/exclude` when appropriate.
