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
  resolve model sources, freeze the effective catalog and policy,
  and resolve portable IDs.
- `s2h-model-probe`: MUST use for the one-time per-run capability probe.
- `s2h-run-ledger-format`, `s2h-plan-audit-format`, `s2h-chunk-index-format`,
  `s2h-requirements-format`, `s2h-step-context-format`,
  `s2h-step-status-format`, `s2h-checkpoint-format`,
  `s2h-doc-context-format`, `s2h-doc-assignment-format`, and
  `s2h-final-report-format`: use to create and validate the corresponding
  `.agent-work` artifacts.
- `s2h-verification-before-completion`: MUST use before reporting any phase or run as complete.

## Role boundaries

The orchestrator only persists ledger state, delegates, and validates handoffs.
It does none of the delegated work itself:

- MUST NOT modify repository files or any `.agent-work` artifact beyond the durable
  records this skill defines (ledger, step statuses, checkpoint copies, reports,
  final report). File modification is delegated to `s2h-StepImplementer` and
  `s2h-DocumentationWriter`.
- MUST NOT run validation commands, tests, format checks, or any verification of its own.
  Verification is delegated: the format checkers in steps 4 and 5, `s2h-StepVerifier`,
  `s2h-FinalVerifier`, and `s2h-DocumentationVerifier`. The step 13 repository check
  confirms ledger records against Git state only; it runs no tests.
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
- The orchestrator is the sole authority for implementation-loop model
  assignments. Agents may recommend models, but they cannot finalize or apply
  them. In the decomposition phase, the `s2h-PlanDecomposer` finalizes
  loop assignments per `s2h-plan-decomposition`; the orchestrator
  validates them at phase acceptance.
- Treat the configured retry limit as repair attempts after the initial
  implementation attempt; a verification loop that exhausts its allowance
  becomes `blocked`.
- File-modifying agents must finish with validation and a commit. Verification
  agents are read-only.
- Do not commit `.agent-work/`.
- A missing or malformed model assignment in a handoff is `BLOCKED`. Silent
  parent-model substitution is forbidden; a fallback or default usage must be
  recorded as a warning with the exact reason.
- Every delegation parameter resolved in step 7 MUST be applied as written; omitting or
  degrading any parameter to continue is forbidden and makes that delegation `blocked`,
  with the exact resume action recorded.

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

4. **Audit the plan.** (delegation: s2h-PlanAuditor, then one format checker per
   documentation context file)
   - Unless `Skip plan audit` is `true`: persist `phase: s2h-plan-audit`,
     `status: running`, and `attempt: 1`; delegate exactly once to `s2h-PlanAuditor`
     with only the plan path from `run.json` and the run directory. Validate its
     handoff using `s2h-handoff` and `s2h-plan-audit-format`, validate the
     `s2h-plan-audit.json` the auditor wrote in the run directory, and record in run
     state the path of the `requirements.json` the auditor wrote.
   - Then delegate one read-only format check per documentation context file to a
     cheap subagent that applies `s2h-doc-context-format`. Resolve each model per step 7
     as the cheapest portable ID satisfying a read-only capability. Send the format
     check template verbatim and explicitly tell it to use both skills. Accept only
     verified reports per `s2h-handoff`.
   - Branches:
     - Any failed check persists `blocked` and stops.
     - A `NEEDS_CLARIFICATION` status reports the required questions to the user and
       stops as `blocked`.
     - A `BLOCKED` status reports the findings and stops as `blocked`.
     - When `Skip plan audit` is `true`, write the `SKIPPED` record defined by
       `s2h-plan-audit-format` in the run directory with
       `documentation_context.status: UNAVAILABLE`, and proceed to decomposition.
       Later documentation assignments must then be built from verified implementation evidence
       rather than a plan brief.

5. **Decompose the plan.** (delegation: s2h-PlanDecomposer, then one format checker per step file)
   - Persist `phase: decomposition`, `status: running`. Delegate to
     `s2h-PlanDecomposer` for the initial decomposition exactly once, with the
     run's per-loop retry cap and the file paths:
     - The persisted `s2h-plan-audit.json`.
     - When the audit ran, `requirements.json`

     It owns the whole phase end to end. Accept only `PASS`.

   - Validate using `s2h-chunk-index-format`:
     - Every step file path exists.
     - Each inventory requirement is assigned to exactly one chunk.
     - Dependencies form an acyclic graph
     - Within its chunk every behavioral unit keeps its primary-test step immediately
       before its implementation step
     - Every chunk's `doc_status` is `completed`.
   - Delegate one read-only format check per step file to a cheap subagent that
     applies `s2h-step-context-format`. Resolve each model per step 7 as the cheapest
     portable ID satisfying a read-only capability. Send the format check template
     verbatim and explicitly tell it to use both skills. Accept only verified reports
     per `s2h-handoff`. Branches:
     - All pass: continue to step 6.
     - Any fail: increment the decomposition attempt counter, re-delegate
       `s2h-PlanDecomposer` with the targeted-repair block from
       `references/delegation-prompts.md` listing each failing step file and its
       findings one per line; accept only PASS, then rerun format checks on the
       previously failing step files only.
     - Any check still failing after L repair rounds: persist `blocked` and stop.

6. **Select the next step.** (bookkeeping)
   - Load `chunk-index.json` once when entering this phase. Keep that copy in context
     and reuse it for every later selection in a continuous session.
     MUST reread when resuming or after compaction.
   - Choose the first step in dependency order that is not `completed`, and whose
     dependencies are all `completed`. If all steps are completed, continue to final
     verification. For a selected step, create or load `steps/<step-id>-status.json`
     using `s2h-step-status-format` and preserve its attempt count.

7. **Resolve the step assignment before every delegated call.** (bookkeeping)
   - Use the catalog and policy loaded in step 2. MUST reread when resuming or after compaction.
     On resume, confirm their fingerprints are unchanged before use.
   - Evaluate role requirements (`required_capabilities`, `minimum_tier`) for the
     delegation.
   - Select a portable ID:
     - The decomposer recommendation for this step/role from `chunk-index.json` when present
       and satisfying those constraints.
     - Else the role's policy default.
   - Record the selection source.
   - Resolve the host selector and apply the single policy-fallback retry and
     config-failure handling per `s2h-model-routing-adapter`'s catalog lookup and
     fallback order.
   - Persist the pre-delegation assignment - requested portable ID, resolved model name,
     selection source, fallback used if any.
   - Delegate passing every delegation parameter per `s2h-model-routing-adapter`, with
     a `model` field only when confirmed.
   - After delegation, persist the application result per the probed evidence channel:
     runtime model (tool-reported payload first, self-ID otherwise), `evidence`, and any warnings.
     Never claim dynamic selection when status is `routing-unavailable`.

8. **Implement and verify the selected step.** (delegation: s2h-StepImplementer, then
   s2h-StepVerifier, per cycle)
   - Persist the step as `running` before delegating `s2h-StepImplementer`. Pass only
     file paths: the step context, its latest checkpoint, and the latest relevant verifier
     report.
   - Validate the implementer handoff:
     - `PASS` may proceed to verification.
     - `RECOVERABLE` persists the recovery state and stops
     - `BLOCKED` persists the blocker and stops.
     - A missing or malformed handoff is `blocked` and does not consume a retry.
   - Persist the step as `running` before delegating `s2h-StepVerifier`. Validate the
     verifier handoff:
     - `VERIFIED` marks the step `completed` and records its evidence and commit.
     - `INCOMPLETE` marks it `verification-failed`, increments the repair-attempt counter,
       and returns to the implementer if the counter is at most the configured retry limit.
     - `BLOCKED` stops without consuming a retry.
   - **Never mark a step `completed` from an implementer `PASS`.**
   - After each handoff: copy status, requirement evidence, validation evidence,
     artifacts, repository state, blockers, and `resume_from` into the durable ledger
     before making the next delegation.

9. **Verify the complete implementation.** (delegation: s2h-FinalVerifier)
   - After every step is `completed`, persist `phase: final-verification`,
     `status: running`. Delegate exactly once to `s2h-FinalVerifier` with only file paths:
     the plan from `run.json`, `chunk-index.json`, every persisted handoff report, and
     the ledger's commit and repository state.
   - Branches:
     - `VERIFIED` continues
     - `INCOMPLETE` identifies the affected steps, consumes one final-verification repair
       attempt recorded as `final_verification_repairs` in `run.json`, and returns to step 8
       within the retry limit.
     - `BLOCKED` stops
   - **Do not begin documentation until final verification is `VERIFIED`.**
   - Final verification covers implementation only; pre-existing documentation
     is out of scope for this check, and its absence or staleness MUST NOT count
     against `VERIFIED`.

10. **Document source files.** (delegation: s2h-DocumentationWriter per assignment)
   - Build documentation assignments only for changed source files that require
     maintainer-facing documentation, selected only after final verification; they never
     inherit the decomposer step recommendations as final state. Pass each writer the path
     of `documentation/source-doc-context.md` from the plan audit as the initial brief;
     refine the assignment with the final changed files and relevant step reports; the
     implementation evidence is authoritative if it differs from the plan brief.
   - Delegate `s2h-DocumentationWriter` instances in parallel only when their files and
     ownership do not overlap; otherwise delegate sequentially. Persist each assignment
     before and after delegation. Require `PASS` plus a separate documentation commit, or
     `changed_files: []` with a material no-op explanation, or an explicit `N/A` Git
     explanation. A `RECOVERABLE` or `BLOCKED` result stops the documentation phase.

11. **Verify source documentation.** (delegation: s2h-DocumentationVerifier per assignment)
   - Delegate `s2h-DocumentationVerifier` for every completed s2h-source-doc assignment.
     Branches:
     - `VERIFIED` accepts the assignment.
     - `INCOMPLETE` returns only that assignment to the documentation agent within the retry limit.
     - `BLOCKED` stops.
   - Do not request stylistic changes that are not material findings.

12. **Create and verify user documentation.** (delegation: s2h-DocumentationWriter,
    then s2h-DocumentationVerifier)
   - Create the `s2h-user-doc` assignment, passing `documentation/user-doc-context.md`
     referenced by `s2h-plan-audit.json`, adding the final verified requirements, and
     repository-specific examples. Do not require the Documentation Writer to reread the
     complete plan when the Markdown brief and implementation context cover the
     assignment; the final implementation remains authoritative.
   - Delegate `s2h-DocumentationWriter`, then delegate `s2h-DocumentationVerifier` with
     the paths of both files. Require `VERIFIED` before finalization; apply the same bounded
     retry rule and stop on `BLOCKED` or malformed handoffs.

13. **Finalize.** (bookkeeping)
   - Confirm the ledger's repository state against Git: recorded branch, existing commit
     hashes, and clean tracked changes. Build `final-report.json` using
     `s2h-final-report-format` from the ledger and all verified handoffs, including audit
     status, completed steps, commands and results, commits, traceability,
     branch/worktree state, documentation, warnings, and resume instructions. Atomically
     persist the final report before reporting completion. Completion is legal only when
     final verification and all required documentation verification are `VERIFIED` and the
     repository check passes.

14. **Report directly to the user.** (bookkeeping)
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

If the agent's final message lacks a valid summary, points at a missing or
unreadable saved report, or reports an unsupported status, missing evidence,
or contradictory repository fields, record `blocked` with the raw failure
description and exact resume action. Do not reinterpret the result as
`INCOMPLETE`, retry it automatically, repair its artifacts, or continue to
another phase.
A handoff that deviates in any way from the exact `s2h-handoff` schema - including
status vocabulary (eg. `COMPLETED` where `PASS` is required) and field naming - MUST NOT be
corrected, normalized, or edited by the orchestrator. It is `blocked`, with the deviation
described and the exact resume action recorded. Resumption re-delegates that one delegation
on a later invocation, and persisted checkpoints mean no completed work is redone.

## Delegation prompt templates

Before your first delegation in a session, MUST read `references/delegation-prompts.md`.
Every delegation prompt MUST contain ONLY the verbatim block lines for that role from
`references/delegation-prompts.md`. They MUST NOT restate acceptance criteria,
requirement IDs, or any status vocabulary. Every block follows the same line order:
Role, Task ID and attempt, Paths (and any named persisted values), Skills and
Instructions (both present only on generic subagent launches; named agents carry their
skill bindings and task contract through their agent definitions), and Constraint.
Never inline plan text, step contracts, inventory entries, prior narratives, or model
reasoning; each agent saves its complete handoff per `s2h-handoff` under
`<run-dir>/reports/` and returns only a summary naming `status` and that path.

Verbatim versus fill-in: the line labels (`Role:`, `Task ID and attempt:`, `Paths:`,
`Skills:`, `Instructions:`, `Constraint:`), the bullet markers, and each Constraint
sentence are sent exactly as written. Only placeholder values are substituted at
delegation time. Every Paths entry MUST be a concrete file or directory path: bounded
sets enumerate each path on its own indented bullet line under the set header; whole-run
collective inputs pass the containing directory with the completeness phrasing shown in
the block.

Placeholders:
- `<plan-path>` is the immutable plan path from `run.json`.
- `<run-dir>` is the run directory.
- `<step-id>` is the selected step identity.
- `<L>` is the per-loop retry cap from `run.json`.
- `<n>` is the 1-based attempt number from persistent state.

## State machine
`pending -> running -> verification-failed -> running -> completed`, with
`interrupted`, `recoverable`, `blocked`, or `abandoned` as durable outcomes.
`NEEDS_CLARIFICATION` from plan audit maps to `blocked` pending a user decision.
`INCOMPLETE` consumes one repair attempt; `BLOCKED` never consumes a repair attempt.

## Outputs
Maintain `run.json`, `s2h-plan-audit.json`, `requirements.json`,
`chunk-index.json`, `steps/<step-id>.md`,
`steps/<step-id>-status.json`, `checkpoints/<step-id>.json`, `reports/*.json`,
documentation assignment Markdown files, commit hashes, and `final-report.json`.
Report completed work, validation evidence, blockers, and resume instructions per
`s2h-handoff`.

## Related agents

- s2h-OrchestratorAgent
- s2h-PlanAuditor
- s2h-PlanDecomposer
- s2h-StepImplementer
- s2h-StepVerifier
- s2h-FinalVerifier
- s2h-DocumentationWriter
- s2h-DocumentationVerifier
