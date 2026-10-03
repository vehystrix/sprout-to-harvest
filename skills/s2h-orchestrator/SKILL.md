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
```

Reject the invocation as `BLOCKED` if `Plan` or `Run directory` is missing,
the retry value is not a non-negative integer, or `Skip plan audit` is not
explicitly `true` or `false`. Resolve the run directory relative to the target
repository and do not silently select a different run.

## Related skills
- `s2h-persistent-state`: use for the run ledger, checkpoints, recovery
  states, and resume decisions.
- `s2h-git-isolation`: use before starting a Git-tracked run and when
  enforcing branch/commit policy.
- `s2h-subagent-recovery`: use whenever a delegated agent is interrupted or blocked.
- `s2h-requirements-traceability`: use to coordinate requirement, step, commit,
  validation, and documentation coverage.
- `s2h-handoff`: use to validate every delegated agent's final handoff before consuming it.
- `s2h-model-catalog-format` and `s2h-model-routing-adapter`: use to freeze the effective
  catalog and policy, run the one-time capability probe, and resolve portable IDs.
- `s2h-run-ledger-format`, `s2h-plan-audit-format`, `s2h-chunk-index-format`,
  `s2h-requirements-format`, `s2h-step-context-format`,
  `s2h-step-status-format`, `s2h-checkpoint-format`,
  `s2h-doc-context-format`, `s2h-doc-assignment-format`, and
  `s2h-final-report-format`: use to create and validate the corresponding
  `.agent-work` artifacts.
- `s2h-verification-before-completion`: use before reporting any phase or run as complete.

## Rules
Keep the original plan immutable. Never load its body into orchestrator
context; pass only its path in every delegation, and delegate plan reading
to the roles that need the content.
- The orchestrator is the sole authority for implementation-loop model
  assignments. Agents may recommend models, but they cannot finalize or apply
  them. In the decomposition phase, the `s2h-PlanDecomposer` finalizes
  documentation-loop assignments per `s2h-plan-decomposition`; the orchestrator
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

Before consuming a handoff, validate the schema version, every mandatory
top-level field, status-specific resume rules, requirement evidence,
validation evidence, changed-file and commit reporting, and repository state.
A failed check is `BLOCKED` and is never retried as an ordinary verification
failure.

## Execution procedure

Follow this procedure in order. Do not skip a phase, reorder steps, or launch
a later phase because an earlier agent's narrative sounds complete.

1. **Load or initialize the run.** If the run directory does not exist, create
   it and atomically write `run.yaml` using `s2h-run-ledger-format` with the inputs,
   `phase: initialization`, `status: pending`, `attempt: 0`, and the current
   timestamp before delegating. If it exists, read `run.yaml` using
   `s2h-run-ledger-format`, `chunk-index.yaml` using `s2h-chunk-index-format`, and the
   latest `reports/*.yaml` using `s2h-handoff`; validate that the stored plan
   path, run directory, retry limit, and audit setting match the invocation.
   Resume the first non-completed phase or step selected by the
   persistent-state rules. Never overwrite a completed result.
2. **Confirm effective configuration and run the capability probe.** Load the
   effective catalog and policy (repository files, merged overrides confirmed
   as required), canonicalize both, copy them under `.agent-work/<run-id>/`,
   and calculate `sha256:` fingerprints. Run the capability probe exactly once
   per the `s2h-model-routing-adapter` skill; it determines whether the delegation
   tool surface accepts a per-delegation `model` parameter and pins the evidence
   channel. Persist `model_routing` in `run.yaml`: `catalog_source`, `policy_source`,
   `adapter` (active host identifier), `preflight: { status, mechanism, evidence_channel }`,
   fingerprints, and warnings including any routing-unavailable warning. If probe status is
   `routing-unavailable` and `require_application` is true, persist `blocked` and stop; otherwise
   continue - every later delegation omits the `model` field and records a
   routing-unavailable warning with `applied: false`.
3. **Prepare repository isolation.** Inspect Git before any file-modifying
   delegation. If Git exists, apply `s2h-git-isolation`, record the
   starting branch and commit, require clean tracked changes, and create or
   reuse the recorded implementation branch. If Git is unavailable, record the
   limitation and use `N/A` repository fields. If the required Git precondition
   fails, persist `blocked` and stop.
4. **Audit the plan.** Unless `Skip plan audit` is `true`, persist
   `phase: s2h-plan-audit`, `status: running`, and `attempt: 1`; delegate exactly once
   to `s2h-PlanAuditor` with only the plan path from `run.yaml` and the run
   directory. Validate its handoff using `s2h-handoff` and
   `s2h-plan-audit-format`, validate the `s2h-plan-audit.yaml` the auditor wrote in
   the run directory, record in run state the path of the
   `requirements.yaml` the auditor wrote. Then delegate one read-only
   format check per documentation context file to a cheap subagent that applies
   `s2h-doc-context-format`, resolving each model per step 7 as the cheapest
   portable ID satisfying a read-only capability, and accept only verified reports
   per `s2h-handoff`. Explicitly tell it to use both skills. On any failed check,
   persist `blocked` and stop. Then branch on its status:
   `NEEDS_CLARIFICATION` reports the required questions to the user and stops as
   `blocked`; `BLOCKED` reports the findings and stops as `blocked`. When
   `Skip plan audit` is `true`, the orchestrator writes the `SKIPPED` record
   defined by `s2h-plan-audit-format` in the run directory, with
   `documentation_context.status: UNAVAILABLE`, and proceeds to decomposition;
   later documentation assignments must then be built from verified
   implementation evidence rather than a plan brief.
5. **Decompose the plan.** Persist `phase: decomposition`, `status: running`.
   Delegate exactly once to `s2h-PlanDecomposer` with only file paths - the plan
   from `run.yaml`, the persisted `s2h-plan-audit.yaml`, and - when the audit ran -
   `requirements.yaml`; when the audit was skipped, it derives the inventory
   itself. You pass the run's per-loop retry cap in that delegation; it owns the whole
   phase end to end. Accept only `PASS`. On return, validate using `s2h-chunk-index-format`:
   every step file path exists, each inventory requirement is assigned to
   exactly one chunk, dependencies form an acyclic graph, and every behavioral
   unit keeps its primary-test step immediately before its implementation
   step within its chunk, and every chunk's `doc_status` is `completed`. Then
   delegate one read-only format check per step file to a cheap subagent that
   applies `s2h-step-context-format`; resolve each model per step 7 as the cheapest
   portable ID satisfying a read-only capability, and accept only verified
   reports per `s2h-handoff`. On any failed check, persist `blocked` and stop.
6. **Select the next step.** Load `chunk-index.yaml` using
   `s2h-chunk-index-format` once when entering this phase; keep that copy in context
   and reuse it for every later selection in a continuous session; reload only when resuming.
   Choose the first step in dependency order that is not `completed`. Do
   not select a step whose dependencies are not `completed`. If all steps
   are completed, continue to final verification. For a selected step,
   create or load `steps/<step-id>-status.yaml` using `s2h-step-status-format` and
   preserve its attempt count.
7. **Resolve the step assignment from the catalog.** Before each delegated
   call: (1) use the catalog and policy loaded in step 2; do not re-read them
   per delegation; on resume, confirm their fingerprints are unchanged before use.
   (2) evaluate role requirements (`required_capabilities`, `minimum_tier`) for
   the current delegation; (3) select a portable ID - the role's policy
   `default`, which a decomposer recommendation may replace only when it
   satisfies the same validation, recording the selection source; (4) resolve
   the host selector by looking up `models[].id == selected_portable_id` and
   extracting `hosts.<active_host>`; if the mapping is missing, try the policy
   `fallback` portable ID once, and if that also lacks a mapping, stop as
   BLOCKED naming the missing entry when `require_application` is true,
   otherwise continue without a model field with `applied: false` and a warning
   naming the missing entry (config failure); (5) persist the pre-delegation
   assignment - requested portable ID, resolved model name, selection source,
   fallback used if any; (6) delegate - when probe status is passed, set
   `model` to the resolved value on the delegation call, when routing-unavailable
   set no `model` field and record a routing-unavailable warning with
   `applied: false`; (7) after delegation, persist the application result per
   probed evidence channel - runtime model (tool-reported payload first,
   self-ID otherwise), `evidence`, and any warnings. Never claim dynamic
   selection when status is routing-unavailable. There is no preflight step and
   no method-based resolve or apply lifecycle; the orchestrator reads YAML
   directly, probes once, and delegates with a `model` field only when
   confirmed.
8. **Implement and verify the selected step.** For each implementation cycle:
	- Persist the step as `running` before delegating `s2h-StepImplementer`.
	- Pass only file paths: the step context, its latest checkpoint, and
	  the latest relevant verifier report; the delegated agent reads them.
	- Validate the implementer handoff. `PASS` may proceed to verification;
	  `RECOVERABLE` persists the recovery state and stops; `BLOCKED` persists the
	  blocker and stops. A missing or malformed handoff is `blocked` and does not
	  consume a retry. This stop on `RECOVERABLE` is implementation-loop only;
	  the decomposition loops proceed per `s2h-plan-decomposition`.
	- Persist the step as `running` before delegating `s2h-StepVerifier`.
	- Validate the verifier handoff. `VERIFIED` marks the step `completed` and
	  records its evidence and commit. `INCOMPLETE` marks it
	  `verification-failed`, increments the repair-attempt counter, and returns
	  to the implementer if the counter is at most the configured retry limit.
	  `BLOCKED` stops without consuming a retry. Never mark a step `completed`
	  from an implementer `PASS`.
	- After each handoff, copy status, requirement evidence, validation evidence,
	  artifacts, repository state, blockers, and `resume_from` into the durable
	  ledger before making the next delegation.
9. **Verify the complete implementation.** After every step is `completed`,
   persist `phase: final-verification`, `status: running`; delegate exactly
   once to `s2h-FinalVerifier` with only file paths - the plan from `run.yaml`,
   `chunk-index.yaml`, every persisted handoff report, and the ledger's commit
   and repository state. `VERIFIED` continues; `INCOMPLETE` identifies the
   affected steps, consumes one final-verification repair attempt recorded as
   `final_verification_repairs` in `run.yaml`, and returns to step 8 within
   the retry limit; `BLOCKED` stops. Do not begin documentation
   until final verification is `VERIFIED`.
10. **Document source files.** When implementation is verified, build
    documentation assignments only for changed source files that require
    maintainer-facing documentation. Pass each writer the path of
    `documentation/source-doc-context.md` from the plan audit as
    the initial brief; refine the assignment with the final
    changed files, and relevant step reports; the implementation evidence is
    authoritative if it differs from the plan brief. For independent
    assignments, delegate `s2h-DocumentationWriter` instances in parallel only
    when their files and ownership do not overlap; otherwise delegate
    sequentially. Persist each assignment before and after delegation. Require
    `PASS` plus a separate documentation commit, or `changed_files: []` with a
    material no-op explanation, or an explicit `N/A` Git explanation. A
    `RECOVERABLE` or `BLOCKED` result stops the documentation phase.
    Documentation assignments are selected only after final verification; they
    never inherit the decomposer step recommendations as final state.
11. **Verify source documentation.** Delegate `s2h-DocumentationVerifier` for
    every completed s2h-source-doc assignment. `VERIFIED` accepts the
    assignment; `INCOMPLETE` returns only that assignment to the documentation
    agent within the retry limit; `BLOCKED` stops. Do not request stylistic
    changes that are not material findings.
12. **Create and verify user documentation.** Create the s2h-user-doc
    assignment, passing `documentation/user-doc-context.md`
    referenced by `s2h-plan-audit.yaml`, adding the final
    verified requirements, and repository-specific examples. Do not require the
    Documentation Writer to reread the complete plan when the Markdown brief and
    implementation context cover the assignment; the final implementation
    remains authoritative. Delegate `s2h-DocumentationWriter`, then delegate
    `s2h-DocumentationVerifier` with the paths of both files. Require
    `VERIFIED` before finalization; apply the same bounded retry rule and stop
    on `BLOCKED` or malformed handoffs.
13. **Finalize.** Run the final repository and validation checks. Build
    `final-report.yaml` using `s2h-final-report-format` from the ledger and all
    verified handoffs, including audit status, completed steps, commands and
    results, commits, traceability, branch/worktree state, documentation,
    warnings, and resume instructions. Atomically persist the final report
    before reporting completion. Completion is legal only when final
    verification and all required documentation verification are `VERIFIED`
    and the final repository check passes.
14. **Report directly to the user.** After persisting and validating
    `final-report.yaml`, report it using the user-facing response structure and
    status rules in `s2h-final-report-format`. The response must agree with the
    persisted report.

## Delegation contract

For every delegation, use this sequence exactly:

```text
persist phase/step as running
-> launch the named agent with only the listed context
-> receive exactly one s2h-handoff/v1 report
-> validate schema, allowed status, evidence, artifacts, and repository fields
-> persist the report and derived durable state atomically
-> apply the phase-specific branch above
```

If the agent returns no report, more than one report, an unsupported status,
missing evidence, or contradictory repository fields, record `blocked` with the
raw failure description and exact resume action. Do not reinterpret the result
as `INCOMPLETE`, retry it automatically, or continue to another phase.

## State machine
`pending -> running -> verification-failed -> running -> completed`, with
`interrupted`, `recoverable`, `blocked`, or `abandoned` as durable outcomes.
`NEEDS_CLARIFICATION` from plan audit maps to `blocked` pending a user decision.
`INCOMPLETE` consumes one repair attempt; `BLOCKED` never consumes a repair attempt.

## Outputs
Maintain `run.yaml`, `s2h-plan-audit.yaml`, `requirements.yaml`,
`chunk-index.yaml`, `steps/<step-id>.md`,
`steps/<step-id>-status.yaml`, `checkpoints/<step-id>.yaml`, `reports/*.yaml`,
documentation assignment Markdown files, commit hashes, and `final-report.yaml`.
Report completed work, validation evidence, blockers, and resume instructions using
`s2h-handoff/v1`.

## Related agents

- s2h-OrchestratorAgent
- s2h-PlanAuditor
- s2h-PlanDecomposer
- s2h-StepImplementer
- s2h-StepVerifier
- s2h-FinalVerifier
- s2h-DocumentationWriter
- s2h-DocumentationVerifier
