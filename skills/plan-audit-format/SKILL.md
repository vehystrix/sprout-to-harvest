---
name: plan-audit-format
description: Only use when explicitly invoked
# description: "Defines the persisted YAML structure for plan-audit results."
user-invocable: false
disable-model-invocation: true
---
# Plan Audit Format

Use this skill when the Plan Auditor writes `.agent-work/<run-id>/plan-audit.yaml`.

## Structure

The file is a complete `agent-handoff/v1` YAML report. Its role-specific
`details` value must use this shape:

```yaml
schema: agent-handoff/v1
agent: Plan Auditor
task: run-001 plan-audit
status: PASS
summary: The plan is specific enough to decompose.
inputs:
  context_files:
    - path/to/plan.md
  prior_reports: []
details:
  status: PASS
  findings: []
  external_interfaces: []
  required_questions: []
  validation_gaps: []
  requirements_inventory_path: .agent-work/run-001/requirements-inventory.yaml
  documentation_context:
    status: PROVIDED
    source_file: documentation/source-documentation-context.md
    user_file: documentation/user-documentation-context.md
requirements:
  - id: REQ-001
    result: SATISFIED
    evidence: Plan section "Behavior" defines the expected result.
validation:
  - command: N/A
    result: NOT_RUN
    evidence: Plan audit is a document review.
artifacts:
  changed_files: []
  created_reports:
    - .agent-work/run-001/plan-audit.yaml
  commits: []
repository:
  branch: N/A
  last_commit: N/A
  worktree: UNKNOWN
blockers: []
resume_from: null
```

`details.status` must match the top-level `status`. Use `PASS` only when no
clarification is required. Use `NEEDS_CLARIFICATION` only when
`required_questions` is non-empty. Use `BLOCKED` for missing or unreadable
inputs.

The orchestrator is the sole writer of a `SKIPPED` record, created when plan
auditing is skipped. It is a minimal `agent-handoff/v1` file with
`details.status: SKIPPED`, empty `findings`, no
`requirements_inventory_path`, and `documentation_context.status:
UNAVAILABLE`.

`documentation_context` is a pointer to the plan-level Markdown briefs for later
documentation assignments. `status` is `PROVIDED` when both context files exist,
`EMPTY` when the audit found no documentation obligation, and `UNAVAILABLE` when the
audit was skipped.
`requirements_inventory_path` points to the run's `requirements-inventory.yaml`.
It is present on a `PASS` audit and absent otherwise; a non-PASS audit records no path.

## Validation

Require all `agent-handoff/v1` fields, the six audit detail fields,
`documentation_context` pointer with `status`, `source_file`, and `user_file`, evidence
for every requirement and validation item, `changed_files: []`, `commits: []`, and
`resume_from: null.`
