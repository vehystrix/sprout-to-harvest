---
name: s2h-orchestrator
description: >-
  Orchestrates a resumable, test-driven implementation plan using isolated
  audit, decomposition, implementation, verification, and documentation agents.
user-invocable: true
disable-model-invocation: true
---

## Required input

Before doing any work, require these four values from the user or invocation context:

```text
Plan: <path to the immutable plan>
Run directory: <.agent-work/<run-id>>
Maximum retries per verification loop: <non-negative integer>
Skip plan audit: true | false
Include global model repository: true | false (default: false)
```

Reject the invocation as `BLOCKED` if `Plan` or `Run directory` is missing,
the retry value is not a non-negative integer, or `Skip plan audit` is not
explicitly `true` or `false`. Resolve the run directory relative to the target
repository and do not silently select a different run.

## Model source resolution

Resolve each model file per `s2h-model-routing-adapter`'s model source resolution; the
merge applies when `Include global model repository` is `true`. Validate, canonicalize,
freeze, and fingerprint the merged result per that skill.

## Related skills
- `s2h-compaction-recovery`: MUST invoke at session start and re-read after every compaction.
- `s2h-persistent-state`: MUST use for the run ledger, checkpoints,
  recovery states, and resume decisions.
- `s2h-git-isolation`: use before starting a Git-tracked run and when
  enforcing branch/commit policy.
- `s2h-subagent-recovery`: use whenever a delegated agent is interrupted or blocked.
- `s2h-requirements-traceability`: MUST use to coordinate requirement, step,
  commit, validation, and documentation coverage.
- `s2h-handoff`: MUST use to validate every delegated agent's final handoff before consuming it.
- `s2h-model-catalog-format` and `s2h-model-routing-adapter`: MUST use to
  resolve model sources and freeze the effective catalog and policy; portable ID
  resolution is per-delegation by the delegating tier.
- `s2h-model-probe`: MUST use for the one-time per-run capability probe.
- `s2h-run-ledger-format`, `s2h-plan-audit-format`, `s2h-chunk-index-format`, and
  `s2h-final-report-format`: use to read run state, validate delegated format
  artifacts, and build the final report.
- `s2h-verification-before-completion`: MUST use before reporting any phase or run as complete.

## Role boundaries

The orchestrator only persists ledger state, delegates, and validates handoffs.
It does none of the delegated work itself:

- MUST NOT modify repository files or any `.agent-work` artifact beyond `run.json`,
  `delegations.jsonl`, `final-report.json`, the frozen catalog and policy copies
  written in step 2, and the SKIPPED audit record when plan audit is skipped. Step
  status files, checkpoints, delegation records, and tier reports are owned by their
  spawners per their skills.
- MUST NOT run validation commands, tests, format checks, or any verification of its own.
  Running `scripts/validate_delegations.py` (relative to `s2h-run-ledger-format`)
  on a line you just appended, or the owning format skill's validator
  (`scripts/validate.py`, relative to that skill) on an artifact you authored, is
  ledger bookkeeping, not delegated work; everything else is delegated to the owner tiers.
  The step 9 repository check confirms ledger records against Git state only; it runs no tests.
- MUST NOT repair a failed delegation's artifacts itself, and MUST NOT re-delegate
  the same task automatically. A failed, missing, or malformed handoff is always
  `blocked` per the Delegation contract, with its exact resume action recorded;
  resumption happens on a later invocation, not mid-run.
- MUST NOT edit any delegated agent's handoff or report file, and MUST NOT rewrite
  ledger entries to conceal a protocol deviation. A delegation report is persisted
  atomically when created and immutable afterward; ledger records change only through
  the state transitions this skill defines.
- After any compaction or resume, MUST re-read this skill and
  `references/delegation-prompts.md`, located relative to this skill's location,
  before delegating again. Patterns remembered from earlier in the session do not
  supersede them; durable records are authoritative over narrative memory.

## Rules
Keep the original plan immutable. Never load its body into orchestrator
context; pass only its path in every delegation, and delegate plan reading
to the roles that need the content.
- Model assignments are resolved per delegation by the tier that performs the
  delegation under the frozen catalog and policy via `s2h-model-routing-adapter`;
  agents may recommend models, but only the delegating tier finalizes them.
  The orchestrator holds no catalog or policy in context; at each phase
  acceptance it audits recorded assignments by tail-reading only new lines of
  `delegations.jsonl`, never a full-file reread, per the line check
  defined by `s2h-run-ledger-format`.
- Treat the configured retry limit as repair attempts after the initial
  implementation attempt; a verification loop that exhausts its allowance
  becomes `blocked`.
- File-modifying agents must finish with validation and a commit. Verification
  agents are read-only.
- Do not commit `.agent-work/`.

## Execution procedure

Follow these steps in order, letter for letter. Do not skip a phase, reorder
steps, or begin a later phase because an earlier agent's narrative sounds
complete. Each step states its state transition, its single action, and its
branches; any behavior outside those statements is a deviation from this
procedure.

1. **Load or initialize the run.** (bookkeeping)
   - If the run directory does not exist: create it and atomically write `run.json`
     using `s2h-run-ledger-format` with the inputs, `phase: initialization`,
     `status: pending`, `attempt: 0`, and the current timestamp before delegating.
   - If it exists: read `run.json` using `s2h-run-ledger-format`, `chunk-index.json`
     using `s2h-chunk-index-format`, and the latest `reports/*.json` using
     `s2h-handoff`; validate that the stored plan path, run directory, retry limit,
     and audit setting match the invocation. Resume the first non-completed phase
     or step selected by the persistent-state rules. Never overwrite a completed
     result.

2. **Freeze configuration and probe.** (bookkeeping)
   - Resolve each source per Model source resolution above; load the effective
     catalog and policy, canonicalize both, copy them under `.agent-work/<run-id>/`,
     and calculate `sha256:` fingerprints - for a source with no file, freeze
     nothing and record it as `none`.
   - Run the capability probe exactly once per the `s2h-model-probe` skill; persist
     its result in `run.json.model_routing`, whose block is defined by
     `s2h-run-ledger-format`. If the probe status is `routing-unavailable` and
     `require_application` is true, persist `blocked` and stop; every later
     delegation then follows the adapter's run-level routing-unavailable handling.

3. **Prepare repository isolation.** (bookkeeping)
   - Inspect Git before any file-modifying delegation. If Git exists, apply
     `s2h-git-isolation`, record the starting branch and commit, require clean tracked
     changes, and create or reuse the recorded implementation branch. If Git is
     unavailable, record the limitation and use `N/A` repository fields. If a required
     Git precondition fails, persist `blocked` and stop.

4. **Audit the plan.** (delegation: s2h-PlanAuditor)
   - Unless `Skip plan audit` is `true`: persist `phase: s2h-plan-audit`,
     `status: running`, and `attempt: 1`; delegate exactly once to `s2h-PlanAuditor`
     with only the plan path from `run.json` and the run directory. Validate its
     handoff using `s2h-handoff` and `s2h-plan-audit-format`, validate the
     `s2h-plan-audit.json` the auditor wrote in the run directory, and record in run
     state the path of the `requirements.json` the auditor wrote. You do not
     re-check its documentation context files.
   - Branches:
     - A `DONE` audit records the path of `requirements.json` in run state and
       continues to decomposition; no implementation work starts on assumption.
     - A `BLOCKED` status reports the findings (including any required questions) to the
       user and stops as `blocked`.
     - When `Skip plan audit` is `true`, write the `SKIPPED` record defined by
       `s2h-plan-audit-format` in the run directory with
       `documentation_context.status: UNAVAILABLE`, and proceed to decomposition.
       Later documentation assignments must then be built from verified implementation evidence
       rather than a plan brief.

5. **Decompose the plan.** (delegation: s2h-PlanDecomposer)
   - Persist `phase: decomposition`, `status: running`. Delegate to
     `s2h-PlanDecomposer` for the initial decomposition exactly once, with the
     run's per-loop retry cap and the file paths:
     - The persisted `s2h-plan-audit.json`.
     - When the audit ran, `requirements.json`

    It owns the whole phase end to end. Accept only `DONE`.

   - Validate using `s2h-chunk-index-format`:
     - Every step file path exists.
     - Each inventory requirement is assigned to exactly one chunk.
     - Dependencies form an acyclic graph
     - Within its chunk every behavioral unit keeps its primary-test step immediately
       before its implementation step
     - Every chunk's `doc_status` is `completed`.

6. **Run the implementation phase.** (delegation: s2h-ImplementationPhase)
   - Persist `phase: implementation`, `status: running`. Delegate exactly once to
     `s2h-ImplementationPhase` with only paths and cap L: the run directory,
     the path of `chunk-index.json`, and the per-loop retry cap. You do no selection
     or step work yourself; it reports only its bounded summary.
   - Validate its bounded summary using `s2h-handoff`: a summary pointing at a missing
     or unreadable report is `blocked`, with the raw failure description as its exact
     resume action; never normalize, edit, reinterpret, or auto-retry it.
   - Branches:
     - `DONE` continues to final verification after you confirm every step status file
       reports `completed`. A step is completed only by a verifier `DONE`, never by an
       implementer `DONE`; you verify this against the status files.
     - `BLOCKED` persists the blocker and stops, naming the blocked step and its recorded
       resume action.

7. **Run final verification.** (delegation: s2h-FinalVerificationPhase)
   - Persist `phase: final-verification`, `status: running`. Delegate exactly once to
     `s2h-FinalVerificationPhase` with only paths and cap L: the run directory, the plan
     path from `run.json`, and the per-loop retry cap. You do no verification yourself;
     it reports only its bounded summary. Final verification covers implementation
     only; pre-existing documentation is out of scope for this check, and its absence or
     staleness MUST NOT count against `DONE`.
   - Validate its bounded summary using `s2h-handoff`; when a `DONE` follows an
     `INCOMPLETE` verdict, record the consumed repair attempts as the integer
     `final_verification_repairs`. The affected step ids stay in the tier's saved
     report.
   - Branches:
     - `DONE` continues to documentation. Documentation begins only after final
       verification is `DONE`; tier ordering enforces that; no separate check lives here.
     - `BLOCKED` persists the blocker and stops with its recorded resume action.

8. **Run the documentation phase.** (delegation: s2h-DocumentationPhase)
   - Persist `phase: documentation`, `status: running`. Delegate exactly once to
     `s2h-DocumentationPhase` with only paths and cap L: the run directory, the final
     changed files from the ledger, the path of `documentation/source-doc-context.md`, the
     path of `documentation/user-doc-context.md`, and the per-loop retry cap. You do no
     documentation work yourself; it reports only its bounded summary.
   - Validate its bounded summary using `s2h-handoff`: a summary pointing at a missing
     or unreadable report is `blocked`, with the raw failure description as its exact
     resume action; never normalize, edit, reinterpret, or auto-retry it.
   - Branches:
     - `DONE` continues to finalize.
     - `BLOCKED` persists the blocker and stops, naming the assignment and its recorded
       resume action.

9. **Finalize.** (bookkeeping)
   - Persist `phase: finalization`, `status: running` in `run.json`. Confirm the
     ledger's repository state against Git: recorded branch, existing commit
     hashes, and clean tracked changes. If the check fails, persist `blocked` and stop;
     its exact resume action names the divergence from the ledger's expected state. Only
     when it passes, persist `status: completed`, then build `final-report.json` using
     `s2h-final-report-format` from the ledger and all verified handoffs, including audit
     status, completed steps, commands and results, commits, traceability,
     branch/worktree state, documentation, warnings, and resume instructions. Atomically
     persist the final report before reporting completion. Completion is legal only when
    final verification and all required documentation verification are `DONE` and the
     repository check passes.

10. **Report directly to the user.** (bookkeeping)
   - After persisting and validating `final-report.json`, report it using the user-facing
     response structure and status rules in `s2h-final-report-format`. The response must
     agree with the persisted report.

## Delegation contract

For every delegation, use this sequence exactly:

```text
persist phase/step as running
-> launch the named agent with only the listed context
-> receive a summary naming status and saved report path
-> validate schema, allowed status, evidence, artifacts, and repository fields
-> persist the report and derived durable state atomically
-> apply the phase-specific branch above
```

A final message that lacks a valid summary or points at a missing or unreadable saved report
is `blocked`, with the raw failure description and exact resume action. Do not reinterpret the
result as `INCOMPLETE`, retry it automatically, repair its artifacts, or continue to another
phase. A final message that reports an unsupported status is handled by the deviation rule
below; the saved report file, never the message text, decides classification.
A handoff that deviates from the exact `s2h-handoff` schema - including status
vocabulary (for example, `COMPLETED` where `DONE` is required) and field naming -
MUST be classified before use: when the outcome is derivable from ground truth
(repository state, step status, run ledger), or when the saved handoff's own details and
evidence substantiate the outcome without contradicting its repository fields,
derive the delegation's ledger entry with
`derived_fields` plus a warning naming each derived field, leaving the handoff untouched;
otherwise it is `blocked`, with the deviation described and the exact resume action
recorded. The orchestrator MUST NOT normalize, edit, reinterpret, or
automatically retry a deviating handoff. Resumption re-delegates that one delegation on
a later invocation, and persisted checkpoints mean no completed work is redone.
Model records are owned by the spawner that appends them. You and each tier append
your own delegation line to `delegations.jsonl` before spawning, then compare each
handoff's `model_assignment` value with the resolved identity per
`s2h-model-routing-adapter`. At each phase acceptance you audit only new lines of
that log, tail-reading only new lines and never a full file - using the line
check defined by `s2h-run-ledger-format`; a new line that fails the check is
`blocked`,
with a resume action naming the offending line id.

## Delegation prompt templates

Before your first delegation in a session, MUST read `references/delegation-prompts.md`,
located relative to this skill's directory. Every delegation prompt MUST contain ONLY
the verbatim block lines for that role from that file. They MUST NOT restate acceptance criteria,
requirement IDs, or any status vocabulary. Every block follows the same line order:
Role, Task ID and attempt, Paths (and any named persisted values), and Constraint.
Never inline plan text, step contracts, inventory entries, prior narratives, or model
reasoning; each agent saves its complete handoff per `s2h-handoff` under
`<run-dir>/reports/` and returns only a summary naming `status` and that path.

Verbatim versus fill-in: the line labels (`Role:`, `Task ID and attempt:`,
`Paths:`, `Constraint:`), the bullet markers, and each Constraint sentence are sent
exactly as written. Only placeholder values are substituted at delegation time. Every
Paths entry MUST be a concrete file or directory path: bounded sets enumerate each
path on its own indented bullet line under the set header; whole-run collective inputs
pass the containing directory with the completeness phrasing shown in the block.

Placeholders:
- `<plan-path>` is the immutable plan path from `run.json`.
- `<run-dir>` is the run directory.
- `<step-id>` is the selected step identity.
- `<L>` is the per-loop retry cap from `run.json`.
- `<n>` is the 1-based attempt number from persistent state.

## State machine
`pending -> running -> verification-failed -> running -> completed`, with
`interrupted`, `blocked`, or `abandoned` as durable outcomes.
`BLOCKED` never consumes a repair attempt.

## Outputs
Maintain `run.json`, `delegations.jsonl`, `s2h-plan-audit.json`, `requirements.json`,
`chunk-index.json`, `steps/<step-id>.md`,
`steps/<step-id>-status.json`, `checkpoints/<step-id>.json`, `reports/*.json`,
documentation assignment Markdown files, commit hashes, and `final-report.json`.
Report completed work, validation evidence, blockers, and resume instructions per
`s2h-handoff`.

## Related agents

- s2h-OrchestratorAgent
- s2h-PlanAuditor
- s2h-PlanDecomposer
- s2h-ImplementationPhase
- s2h-FinalVerificationPhase
- s2h-DocumentationPhase
