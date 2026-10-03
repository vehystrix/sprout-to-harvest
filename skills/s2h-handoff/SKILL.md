---
name: s2h-handoff
description: Only use when explicitly invoked
# description: "Defines the JSON schema for every inter-agent handoff and its report."
user-invocable: false
disable-model-invocation: true
---
# Agent Handoff

Every delegated agent must end with one handoff using this exact JSON
shape. The handoff may be saved in the run directory and summarized to
the caller, but the field names and meanings are stable across agents.

Use this skill whenever a delegated agent creates, validates, or reads
a handoff. The handoff is JSON and is the sole communication contract
between agents.

When persisted, save the complete handoff as JSON under
`reports/<phase>-<subject>-<attempt>.json`; `s2h-plan-audit.json` is the
named exception for the s2h-plan-audit handoff and `final-report.json`
is the named exception for the final handoff. Do not persist handoffs
as Markdown or extensionless files.

```json
{
  "schema": "s2h-handoff/v1",
  "agent": "<role name>",
  "task": "<run id, phase, step or assignment>",
  "status": "<PASS | VERIFIED | INCOMPLETE | NEEDS_CLARIFICATION | BLOCKED | RECOVERABLE>",
  "summary": "<one concise sentence>",
  "inputs": {
    "context_files": [],
    "prior_reports": []
  },
  "details": {},
  "requirements": [
    {
      "id": "<requirement id or N/A>",
      "result": "<SATISFIED | PARTIAL | NOT_SATISFIED | NOT_APPLICABLE | BLOCKED>",
      "evidence": "<specific file, test, command, or reason>"
    }
  ],
  "validation": [
    {
      "command": "<exact command or N/A>",
      "result": "<PASS | FAIL | NOT_RUN>",
      "evidence": "<relevant output or reason>"
    }
  ],
  "artifacts": {
    "changed_files": [],
    "created_reports": [],
    "commits": []
  },
  "repository": {
    "branch": "<branch or N/A>",
    "last_commit": "<hash or N/A>",
    "worktree": "<CLEAN | CHANGED | UNKNOWN | N/A>"
  },
  "blockers": [],
  "resume_from": "<exact next action, or null>"
}
```
The machine-readable form is defined by `references/schema.json`; validate a file with
`scripts/validate.py <file>`.

Rules:

- `schema`, `agent`, `task`, `status`, `summary`, `inputs`,
  `details`, `requirements`, `validation`, `artifacts`,
  `repository`, `blockers`, and `resume_from` are mandatory, even when
  their values are empty or `N/A`.
- `PASS` means the assigned work completed without a verification claim;
  `VERIFIED` is reserved for a verifier. `INCOMPLETE`, `BLOCKED`, and
  `RECOVERABLE` must explain the next action in `resume_from`.
- `NEEDS_CLARIFICATION` is reserved for plan audit findings that
  require a user decision before decomposition; it must include the
  questions in `details` and a null `resume_from`.
- Role-specific payloads such as audit findings, step lists, or
  verification matrices belong under `details`; they must not replace
  or redefine the top-level fields.
- Every delegated role must include a required
  `details.model_assignment` object on every delegation, including runs where
  routing is unavailable; there, record `applied: false`, `evidence: unknown`,
  and a `warning` stating routing was unavailable. The object
  records the exact model used for that attempt, including fallback
  and application warnings. `model_assignment` is required even when
  the assignment is unresolved or blocked.
- Allowed role outcomes are:
  - `s2h-PlanAuditor`:
    - `PASS`
    - `NEEDS_CLARIFICATION`
    - `BLOCKED`
  - `s2h-PlanDecomposer`:
    - `PASS`
    - `BLOCKED`
  - `s2h-StepImplementer`:
    - `PASS`
    - `RECOVERABLE`
    - `BLOCKED`
  - `s2h-StepVerifier`, `s2h-FinalVerifier`, and `s2h-DocumentationVerifier`:
    - `VERIFIED`
    - `INCOMPLETE`
    - `BLOCKED`
  - `s2h-ChunkWriter`:
    - `PASS`
    - `RECOVERABLE`
    - `BLOCKED`
  - `s2h-DocumentationWriter`:
    - `PASS`
    - `RECOVERABLE`
    - `BLOCKED`
  - `s2h-WholePlanVerifier` and `s2h-ChunkVerifier`:
    - `VERIFIED`
    - `INCOMPLETE`
    - `BLOCKED`
- Every requirement and validation item needs evidence. A `VERIFIED`
  handoff must associate executable `PASS` validation evidence with
  every material requirement. Do not claim success from changed files
  or an agent's narrative alone.
- Contradictory or missing model evidence must be treated as `BLOCKED`; lower-confidence
  self-reporting is preserved for auditability but never overrides adapter or host evidence.
- File-modifying agents list every changed file and commit hash.
  Read-only agents use empty `commits` and `changed_files`.
- When Git is unavailable, use `N/A` for `branch`, `last_commit`, and
  commits, and explain that limitation in `details` or `blockers`; do
  not invent a commit hash.
- The caller must validate the schema and required fields before
  consuming the handoff. An invalid or missing handoff is `BLOCKED`
  and must be persisted as such.
- The handoff does not replace durable run status.

## Required delegated model assignment block

```json
{
  "details": {
    "model_assignment": {
      "requested": "reasoning-pro",
      "resolved": "Claude Opus 4.8 (copilot)",
      "portable_id": "reasoning-pro",
      "role": "step-verifier",
      "source": "policy",
      "fallback": null,
      "applied": true,
      "adapter": "copilot",
      "evidence": "adapter-confirmed",
      "runtime_model": "Claude Opus 4.8 (copilot)",
      "rationale": "Independent verification of parser behavior.",
      "warning": null
    }
  }
}
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
- `evidence`: `adapter-confirmed`, `host-reported`,
  `self-reported`, `tool-reported`, or `unknown`.
- `runtime_model`: model reported by the host or delegated agent when available.
- `rationale`: concise selection explanation.
- `warning`: required when the actual result differs from the requested assignment.

The model assignment is attached to the delegation input and copied into the resulting handoff.
