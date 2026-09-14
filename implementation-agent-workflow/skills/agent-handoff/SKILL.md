---
name: agent-handoff
description: "Defines the YAML schema for every inter-agent handoff and persisted handoff report."
---
# Agent Handoff

Every delegated agent must end with one handoff using this exact YAML shape. The handoff may be saved in the run directory and summarized to the caller, but the field names and meanings are stable across agents.

Use this skill whenever a delegated agent creates, validates, or reads a handoff. The handoff is YAML and is the sole communication contract between agents.

When persisted, save the complete handoff as YAML under `reports/<phase>-<subject>-<attempt>.yaml`; `plan-audit.yaml` is the named exception for the plan-audit handoff and `final-report.yaml` is the named exception for the final handoff. Do not persist handoffs as Markdown or extensionless files.

```yaml
schema: agent-handoff/v1
agent: <role name>
task: <run id, phase, step or assignment>
status: PASS | VERIFIED | INCOMPLETE | NEEDS_CLARIFICATION | BLOCKED | RECOVERABLE
summary: <one concise sentence>
inputs:
  context_files: []
  prior_reports: []
details: {}
requirements:
  - id: <requirement id or N/A>
    result: SATISFIED | PARTIAL | NOT_SATISFIED | NOT_APPLICABLE
    evidence: <specific file, test, command, or reason>
validation:
  - command: <exact command or N/A>
    result: PASS | FAIL | NOT_RUN
    evidence: <relevant output or reason>
artifacts:
  changed_files: []
  created_reports: []
  commits: []
repository:
  branch: <branch or N/A>
  last_commit: <hash or N/A>
  worktree: CLEAN | CHANGED | UNKNOWN | N/A
blockers: []
resume_from: <exact next action, or null>
```

Rules:

- `schema`, `agent`, `task`, `status`, `summary`, `inputs`, `details`, `requirements`, `validation`, `artifacts`, `repository`, `blockers`, and `resume_from` are mandatory, even when their values are empty or `N/A`.
- `PASS` means the assigned work completed without a verification claim; `VERIFIED` is reserved for a verifier with executable evidence. `INCOMPLETE`, `BLOCKED`, and `RECOVERABLE` must explain the next action in `resume_from`.
- `NEEDS_CLARIFICATION` is reserved for plan audit findings that require a user decision before decomposition; it must include the questions in `details` and a null `resume_from`.
- Role-specific payloads such as audit findings, step lists, or verification matrices belong under `details`; they must not replace or redefine the top-level fields.
- Every delegated role must include a required `details.model_assignment` object when routing is active. The object records the exact model used for that attempt, including fallback and application warnings. `model_assignment` is required even when the assignment is unresolved or blocked.
- Allowed role outcomes are: plan auditor `PASS` or `NEEDS_CLARIFICATION` or `BLOCKED`; decomposer `PASS` or `BLOCKED`; implementer/documentation agent `PASS`, `RECOVERABLE`, or `BLOCKED`; step/final/documentation verifier `VERIFIED`, `INCOMPLETE`, or `BLOCKED`.
- Every requirement and validation item needs evidence. A `VERIFIED` handoff must associate executable `PASS` validation evidence with every material requirement. Do not claim success from changed files or an agent's narrative alone.
- Contradictory or missing model evidence must be treated as `BLOCKED`. Lower-confidence self-reporting is preserved for auditability but cannot override an explicit adapter or host contradiction.
- File-modifying agents list every changed file and commit hash. Read-only agents use empty `commits` and `changed_files`.
- When Git is unavailable, use `N/A` for `branch`, `last_commit`, and commits, and explain that limitation in `details` or `blockers`; do not invent a commit hash.
- The caller must validate the schema and required fields before consuming the handoff. An invalid or missing handoff is `BLOCKED` and must be persisted as such.
- A handoff with `status: VERIFIED` must contain at least one `PASS` validation item with executable evidence for every material requirement. A handoff with `status: PASS` is not a verification result.
- The handoff does not replace durable run status; the orchestrator copies its status, evidence, artifacts, blockers, and resume point into the run ledger.

## Required delegated model assignment block

```yaml
details:
  model_assignment:
    requested: reasoning-pro
    resolved: Claude Opus 4.8 (copilot)
    portable_id: reasoning-pro
    role: step-verifier
    source: policy
    fallback: null
    applied: true
    adapter: copilot
    evidence: adapter-confirmed
    runtime_model: Claude Opus 4.8 (copilot)
    rationale: "Independent verification of parser behavior."
    warning: null
```

The assignment block records the exact routing state for the current attempt. The fields mean:

- `requested`: ID explicitly requested by policy, user, or agent recommendation.
- `resolved`: host-specific model name or the actual selected runtime model.
- `portable_id`: catalog ID used for validation.
- `role`: stable workflow role, not an agent name.
- `source`: `user`, `policy`, `decomposer`, `orchestrator`, or `fallback`.
- `fallback`: portable ID used after the original request could not be applied.
- `applied`: whether the host confirmed use of the resolved model.
- `adapter`: adapter that handled resolution and application.
- `evidence`: `adapter-confirmed`, `host-reported`, `self-reported`, or `unknown`.
- `runtime_model`: model reported by the host or delegated agent when available.
- `rationale`: concise selection explanation.
- `warning`: required when the actual result differs from the requested assignment.

The model assignment is attached to the delegation input and copied into the resulting handoff. A self-reported runtime model may remain in the record, but it is lower confidence than adapter-confirmed or host-reported evidence and may not override contradictory host or adapter evidence.
