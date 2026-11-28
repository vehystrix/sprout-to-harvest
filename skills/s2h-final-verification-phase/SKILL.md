---
name: s2h-final-verification-phase
description: Only use when explicitly invoked
# description: "Final verification phase contract for the s2h-FinalVerificationPhase tier."
user-invocable: false
disable-model-invocation: true
---
# Final Verification Phase

The final verification phase owns the final-verification loop of one run:
it delegates `s2h-FinalVerifier`, identifies affected steps on an INCOMPLETE
verdict, re-invokes `s2h-StepLoop` per affected step within cap L, and reruns
FinalVerifier until clean or exhausted. It performs no verification itself.

Final verification covers implementation only; pre-existing documentation is
out of scope for this check, and its absence or staleness MUST NOT count
against DONE. No documentation check lives in this loop.

## Input

Input is the run directory, the plan path from `run.json`, and the per-loop
retry cap L.

## Loop

1. Resolve the final-verifier model per Model resolution below; append its
   delegation line to `delegations.jsonl` before spawning. Delegate exactly
   once with only file paths, using the verbatim block below: the plan,
   `chunk-index.json`, every persisted handoff report under `<run-dir>/reports/`,
   and the commit and repository state as recorded in `run.json`.
2. Validate the returned handoff against `s2h-handoff` before consuming it; a
   summary pointing at a missing or unreadable report is BLOCKED with the raw
   failure description as resume action, never reinterpretation.
3. Branches:
   - `DONE`: report DONE per Bounded summary below.
   - `INCOMPLETE`: identify the affected step ids from the report's findings.
     For each affected step, delegate one `s2h-StepLoop` using its verbatim
     block with that step's paths and cap L; validate each StepLoop handoff per
     step 2. When every repair StepLoop returns, rerun FinalVerifier per step 1.
   - `BLOCKED`: report BLOCKED with the recorded resume action; no repair
     attempt is consumed.

FinalVerifier invocations total at most 1 + L: one initial pass plus up to L
re-runs after repair rounds. A finding on the (L+2)nd pass, or a StepLoop that
returns BLOCKED during repair - including "retries exhausted" - stops the loop
as BLOCKED naming that step and its exact resume action. Never auto-redelegate
a blocked task; no BLOCKED consumes a repair attempt.

## Model resolution

Resolve the delegated role (`final-verifier`) at delegation time per
`s2h-model-routing-adapter`. Read the frozen run copies of catalog and policy
under the run directory and the probe status from
`run.json.model_routing.preflight.status`; on resume, confirm their fingerprints
are unchanged before use. Evaluate the role's policy `required_capabilities`
and `minimum_tier`, then select a portable ID: the chunk index recommendation
for this step and role when present and satisfying those constraints, else the
role's policy default; record the selection source. Resolve the host mapping
and apply the single policy-fallback retry and config-failure handling per the
adapter's catalog lookup and fallback order. When the status is
`routing-unavailable`, every delegation follows the adapter's run-level
routing-unavailable handling.

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

**s2h-FinalVerifier** (one delegation per pass)

```text
Role: s2h-FinalVerifier
Task ID and attempt: final-verification, attempt <n>
Paths and values:
  - Run directory: <run-dir>
  - Plan: <plan-path>
  - Chunk index: <run-dir>/chunk-index.json
  - Handoff reports: every persisted report under <run-dir>/reports/
  - Commit and repository state: as recorded in <run-dir>/run.json
Constraint:
  - read-only; MUST NOT modify repository files.
  - MUST read the `AGENTS.md` at the repository root, plus any `AGENTS.md` in a
    subdirectory of that repo containing the files your work targets; if none exist,
    proceed without one; apply everything that is relevant to your work
```

**s2h-StepLoop** (one per affected step, repair rounds only)

```text
Role: s2h-StepLoop
Task ID and attempt: <step-id>, attempt <n>
Paths and values:
  - Run directory: <run-dir>
  - Step context: <run-dir>/steps/<step-id>.md
  - Latest checkpoint: <run-dir>/checkpoints/<step-id>.json (when one exists)
  - Per-loop retry cap L: <L>
Duties:
  - persist this step's status file and append each delegation to delegations.jsonl
Constraint:
  - MUST NOT write or modify repository files, run verification, tests, or repairs;
    delegate that work to subagents
  - report only your bounded summary
  - BLOCKED is a valid terminal outcome: once cap L is consumed or a blocker is
    recorded, stop and report it with its exact resume action; do not spend further
    attempts reaching DONE
```

Placeholders: `<plan-path>` is the immutable plan path from `run.json`;
`<run-dir>` is the run directory; `<step-id>` names an affected step; `<n>` is
the 1-based attempt number of the delegation from persistent state. After any
compaction or resume, MUST re-read this skill before delegating again; patterns
remembered from earlier in the session do not supersede the verbatim templates
above.

## Bounded summary and blocked semantics

Report one fixed-size result: `status` plus the saved report path; when a DONE
follows an INCOMPLETE verdict, add the affected step ids and the consumed
repair attempts so the orchestrator can record them as
`final_verification_repairs`; on BLOCKED add its exact resume action. No
narrative text, no repetition of acceptance criteria. Never auto-redelegate a
BLOCKED task; no BLOCKED consumes a repair attempt.

## Related skills

- `s2h-compaction-recovery`: MUST invoke at session start and re-read after every compaction.
- `s2h-persistent-state`: MUST use for resume decisions and the atomic write rule.
- `s2h-model-routing-adapter`: MUST use to resolve each delegated role's model
  at delegation time, including host mapping lookup and fallback order.
- `s2h-run-ledger-format`: MUST use for the `delegations.jsonl` line format and its validator.
- `s2h-handoff`: MUST use to validate every delegated handoff before consuming it.
