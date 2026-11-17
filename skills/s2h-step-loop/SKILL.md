---
name: s2h-step-loop
description: Only use when explicitly invoked
# description: "Step loop contract for the s2h-StepLoop tier: one step's implementer-verifier cycle."
user-invocable: false
disable-model-invocation: true
---
# Step Loop

The step loop owns exactly one step per invocation: its implementer and
verifier delegations, model resolution for each, handoff validation, counter
increments, and the bounded summary. It never spans steps and never modifies
repository files; file modification belongs to the delegated implementer.

## Input

Input is the selected step's context path, its latest checkpoint path (when
one exists), and the per-loop retry cap `L`.

## Cycle

1. Load or create `steps/<step-id>-status.json` per `s2h-step-status-format`;
   preserve its attempt count across retries.
2. Resolve the implementer model per Model resolution below; append its
   delegation line to `delegations.jsonl` before spawning. Persist the step
   as `running`, then delegate `s2h-StepImplementer` with only file paths,
   using the verbatim block below.
3. Validate the implementer handoff against `s2h-handoff` before consuming it,
   classifying any deviation per `s2h-deviation-classification`. A missing or malformed
   handoff is classified per that rule and does not consume a repair attempt.
4. Implementer branches:
   - `DONE`: proceed to verification.
   - `BLOCKED`: persist the blocker in the step status file and report BLOCKED
     with its recorded resume action. No repair attempt is consumed.
5. Resolve the verifier model, append its delegation line, persist the step as
   `running`, then delegate `s2h-StepVerifier` using the verbatim block below
   with the implementer handoff path; on a repair round the new implementer
   handoff path replaces the prior one.
6. Validate the verifier handoff per step 3 and branch:
   - `DONE`: mark the step `completed` in the status file, recording its
     evidence, commit, artifacts, repository state, blockers, and `resume_from`.
     Only a verifier `DONE` completes the step; never an implementer `DONE`.
     Report DONE.
   - `INCOMPLETE`: persist `verification-failed` and increment the attempt
     counter in the status file. While repair attempts remain - at most `L` after
     the initial attempt, with counters fresh per loop instance - re-delegate
     the implementer per step 2 with its delegation line appended and continue
     from step 3. When the allowance is consumed, report BLOCKED naming "retries
     exhausted" with the findings preserved in the status file.
   - `BLOCKED`: stop without consuming a retry; report BLOCKED with its
     recorded resume action.

## Model resolution

Resolve each delegated role (`implementer`, `verifier`) at delegation time per
`s2h-model-routing-adapter`. Read the frozen run copies of catalog and policy
under the run directory and the probe status from `run.json.model_routing.preflight.status`;
on resume, confirm their fingerprints are unchanged before use. Evaluate the
role's policy `required_capabilities` and `minimum_tier`, then select a
portable ID: the chunk index recommendation for this step and role when present
and satisfying those constraints, else the role's policy default; record the
selection source. Resolve the host mapping and apply the single policy-fallback
retry and config-failure handling per the adapter's catalog lookup and fallback
order. When the status is `routing-unavailable`, every delegation follows the
adapter's run-level routing-unavailable handling.

Append one line to `delegations.jsonl` before each spawn, with exactly the flat
fields defined by `s2h-run-ledger-format`: `id`, `role`,
`requested_portable_id`, `resolved_model`, `selection_source`, `fallback`. Run
its `scripts/validate_delegations.py <file>` after appending and repair the named
line in place until it passes. After each delegation, compare the handoff's
`model_assignment` value with the resolved identity per `s2h-model-routing-adapter`;
never copy a self-report as adapter confirmation.

## Delegation prompt templates

Every delegation MUST be the verbatim block below for that role, with only
placeholder values substituted and nothing else added:

**s2h-StepImplementer** (one delegation per attempt)

```text
Role: s2h-StepImplementer
Task ID and attempt: <step-id>, attempt <n>
Paths:
  - Run directory: <run-dir>
  - Step context: <run-dir>/steps/<step-id>.md
  - Latest checkpoint: <run-dir>/checkpoints/<step-id>.json (when one exists)
  - Verifier report (repair rounds only): <verifier-report-path>
Constraint: file-modifying; work only within the step's declared scope; run
required validation and commit before returning; report the commit hash
```

**s2h-StepVerifier** (one delegation per attempt)

```text
Role: s2h-StepVerifier
Task ID and attempt: <step-id>, attempt <n>
Paths:
  - Run directory: <run-dir>
  - Step context: <run-dir>/steps/<step-id>.md
  - Implementer handoff: <implementer-handoff-path>
  - Relevant checkpoint: <run-dir>/checkpoints/<step-id>.json (when one exists)
Constraint: read-only
```

Placeholders: `<run-dir>` is the run directory; `<step-id>` names the step;
`<n>` is the 1-based attempt number of the delegation from persistent state;
`<implementer-handoff-path>` and `<verifier-report-path>` are saved report paths.
After any compaction or resume, MUST re-read this skill before delegating again;
patterns remembered from earlier in the session do not supersede the verbatim
templates above.

## Bounded summary and blocked semantics

Report one fixed-size result: `status` plus the saved report path. On BLOCKED
add its exact resume action. No narrative text, no repetition of acceptance
criteria. Never auto-redelegate a BLOCKED task; never consume a repair attempt
on BLOCKED; an exhausted loop becomes BLOCKED naming "retries exhausted".

## Related skills

- `s2h-compaction-recovery`: MUST invoke at session start and re-read after
  every compaction.
- `s2h-persistent-state`: MUST use for the step status file, checkpoints, and
  resume decisions.
- `s2h-step-status-format`: MUST use to create and update
  `steps/<step-id>-status.json`.
- `s2h-model-routing-adapter`: MUST use to resolve each delegated role's model
  at delegation time, including host mapping lookup and fallback order.
- `s2h-run-ledger-format`: MUST use for the `delegations.jsonl` line format and
  its validator.
- `s2h-handoff`: MUST use to validate every delegated handoff before consuming
  it.
