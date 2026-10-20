---
name: s2h-handoff
description: Only use when explicitly invoked
# description: "Defines the JSON schema for every inter-agent handoff and its report."
user-invocable: false
disable-model-invocation: true
---
# Agent Handoff

Every delegated agent must end with one handoff using this exact JSON
shape, saved on disk; its final message to the caller contains only a short
summary naming `status` and the path of the saved report. The full handoff
JSON MUST NOT be pasted into that message.

Use this skill whenever a delegated agent creates or validates a handoff.
The handoff is JSON and is the sole communication contract between agents.

Save the complete handoff as JSON under `reports/<phase>-<subject>-<attempt>.json` in
the run directory; `s2h-plan-audit.json` is the named exception for the s2h-plan-audit
handoff and `final-report.json` is the named exception for the final handoff. Do not
save handoffs as Markdown or extensionless files.

```json
{
  "schema": "s2h-handoff/v1",
  "agent": "<role name>",
  "task": "<run id, phase, step or assignment>",
  "status": "<DONE | INCOMPLETE | BLOCKED>",
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
The machine-readable form is defined by `references/schema.json` and validated by
`scripts/validate.py`. The schema is the authoritative specification, the script enforces
the schema but never defines it. Before persisting an artifact of this format: MUST read
the schema, author against it, and run `scripts/validate.py <file>`. The file MUST pass
validation before it may be persisted. Both files are located relative to this skill's
location.

Rules:

- `schema`, `agent`, `task`, `status`, `summary`, `inputs`,
  `details`, `requirements`, `validation`, `artifacts`,
  `repository`, `blockers`, and `resume_from` are mandatory, even when
  their values are empty or `N/A`.
- Set `blockers` non-empty when status is `BLOCKED`, and set `resume_from` to the exact next action.
  Every `BLOCKED` MUST name what the user must do.
- Role-specific payloads such as audit findings, step lists, or
  verification matrices belong under `details`; they must not replace
  or redefine the top-level fields.
- `details.model_assignment` is the model identity the host tool says you are running, exactly
  as reported - or null when no channel exists. Report it as observed; do not infer
  application from name similarity.
- `status` is `DONE`, `INCOMPLETE`, or `BLOCKED`; per-role reporting guidance
  lives in each role's agent file.
- Every `evidence` entry must name a specific file, test, command output, or reason;
  narrative alone does not count.
- File-modifying agents list every changed file and commit hash.
  Read-only agents use empty `commits` and `changed_files`.
- When Git is unavailable, use `N/A` for `branch`, `last_commit`, and
  commits, and explain that limitation in `details` or `blockers`; do
  not invent a commit hash.
- `s2h-handoff/v1` is the value of the `schema` field in the saved file; it names the
  format version, not a path. Never write to a literal path with that name.
- The returned summary points at the saved file: it names `status` and the
  file path only; the caller validates that file, never the message text.
- The handoff does not replace durable run status.
