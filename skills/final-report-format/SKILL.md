---
name: final-report-format
description: Only use when explicitly invoked
# description: "Defines the persisted YAML structure and user-facing
#   response template for the final workflow report."
user-invocable: false
disable-model-invocation: true
---
# Final Report Format

Use this skill when the orchestrator writes `.agent-work/<run-id>/final-report.yaml`.

## Structure

The file is a complete `agent-handoff/v1` report. Put the plan-level
result under `details` using these required fields:

```yaml
details:
  audit_status: PASS
  completed_steps: []
  traceability: []
  documentation:
    source_assignments: []
    user_documentation: []
  warnings: []
  final_repository_check:
    command: git status --short
    result: PASS
    evidence: Working tree is clean except for ignored .agent-work/.
```

`traceability` entries follow the chain defined by `requirements-traceability`.
`completed_steps` must name only steps with a verified handoff. `final_repository_check`
must include an exact command and fresh result. The top-level `status` is `VERIFIED`
only when all required verification and documentation checks are verified.

## User-facing response

After the report is atomically persisted and schema-validated, the
orchestrator must summarize it directly in its response. The user must
not need to open `final-report.yaml` to understand the outcome. Use this
structure, preserving the report's exact status and evidence:

```text
Status: <VERIFIED | INCOMPLETE | BLOCKED | other persisted status>

Completed:
- <verified step or concise statement that no work was completed>

Validation:
- <command>: <result and concise evidence>

Commits:
- <commit hash>: <purpose>

Documentation:
- Source documentation: <verified result, no-op explanation, or status>
- User documentation: <verified result, no-op explanation, or status>

Warnings:
- <warning, or "None">

Resume:
- <exact resume_from action, or "No further action required.">
```

For `VERIFIED`, include the final repository check. For `INCOMPLETE` or `BLOCKED`, put
the status first, name the failed evidence or blocker, and provide the exact
`resume_from` action. Do not claim completion when the persisted status is not
`VERIFIED`; do not omit warnings or blockers.
The response must be derived from the persisted report rather than from
an earlier agent narrative.

## Persistence rules

Write atomically after the final repository check. Do not report
completion before the file exists and its schema validates. Preserve
blockers, warnings, and `resume_from` when the run is incomplete.

## Related skills

- `agent-handoff`
