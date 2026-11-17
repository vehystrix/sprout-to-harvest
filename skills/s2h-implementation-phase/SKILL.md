---
name: s2h-implementation-phase
description: "Implementation phase contract for the s2h-ImplementationPhaseOwner tier."
user-invocable: false
disable-model-invocation: true
---
# Implementation Phase

The `s2h-ImplementationPhaseOwner` owns the whole step-execution phase of one
run: it loads the chunk index, selects steps in dependency order, delegates
exactly one `s2h-StepLoop` per selected step, and tracks every step to
`completed`. It performs no implementation or verification itself.

## Input

Input is the run directory, the path of `chunk-index.json`, and the per-loop
retry cap L from `run.json`. Load the chunk index once on entry; MUST reread
it together with every step status file on resume or after compaction.

## Selection order

1. Read `chunk-index.json` and every `steps/<step-id>-status.json` in the run
   directory.
2. If any step status is `blocked`, stop as BLOCKED naming that step and its
   recorded `resume_from`; never re-delegate it.
3. Otherwise select the first step in dependency order that is not
   `completed` and whose dependencies are all `completed`; a `running` or
   `verification-failed` step outranks any later `pending` step, and resuming
   it re-delegates its StepLoop without redoing completed work.
4. Before delegating, create or load the selected step's status file per
   `s2h-step-status-format` and preserve its attempt count.

## Per-step delegation

- Persist `phase: step-execution` in `run.json` on entry; touch no other field.
- Delegate exactly one `s2h-StepLoop` for the selected step with only file
  paths and cap L, using the verbatim block below.
- Validate every StepLoop handoff against `s2h-handoff` before consuming it: a
  summary pointing at a missing or unreadable report is BLOCKED with the raw
  failure description as resume action; a schema-deviating handoff is never
  normalized, edited, or reinterpreted - derive its outcome from ground truth
  when that supports it, else stop as BLOCKED. Never auto-retry.
- Branches on the bounded summary:
  - `DONE`: continue selection. A step is completed only by a verifier `DONE`;
    the StepLoop enforces that rule and you verify it against the status file.
  - `BLOCKED`: persist the blocker and stop the phase as BLOCKED, naming the
    blocked step and its recorded resume action.

## Delegation prompt template

Every delegation MUST be the verbatim block below, with only placeholder
values substituted:

**s2h-StepLoop** (one delegation per step)

```text
Role: s2h-StepLoop
Task ID and attempt: <step-id>, attempt <n>
Paths and values:
  - Step context: <run-dir>/steps/<step-id>.md
  - Latest checkpoint: <run-dir>/checkpoints/<step-id>.json (when one exists)
  - Per-loop retry cap L: <L>
Constraint: owns this step's implementer-verifier cycle; persists the step
status file and appends to delegations.jsonl; reports only its bounded summary
```

Placeholders: `<run-dir>` is the run directory; `<step-id>` names the selected
step; `<n>` is the 1-based attempt number of this delegation from persistent
state. After any compaction or resume, MUST re-read this skill before
delegating again; patterns remembered from earlier in the session do not
supersede the verbatim template above.

## Bounded repair rule

A StepLoop that returns BLOCKED past its allowance - including a "retries
exhausted" blocker - stops the phase as BLOCKED naming that step and its exact
resume action. The phase never auto-redelegates a blocked task, and no
BLOCKED consumes a repair attempt; resumption happens on a later invocation.

## Blocked conditions

Return BLOCKED when:

- A delegated StepLoop returns BLOCKED, naming that step and its recorded
  resume action;
- A handoff summary points at a missing or unreadable saved report, with the
  raw failure description as the resume action.

Every other failure mode is repairable inside the StepLoop; do not escalate it.

## Completion

Return DONE when every step in `chunk-index.json` has status `completed`. The
bounded summary names `status`, the saved report path, and a pointer to the
step status files: no narrative text, no repetition of acceptance criteria.

## Related skills

- `s2h-compaction-recovery`: MUST invoke at session start and re-read after
  every compaction.
- `s2h-persistent-state`: MUST use for step status files, resume decisions,
  and the atomic write rule.
- `s2h-step-status-format`: MUST use to create and read
  `steps/<step-id>-status.json`.
- `s2h-chunk-index-format`: use to read chunk structure and dependencies.
- `s2h-handoff`: MUST use to validate every delegated handoff before consuming
  it.
