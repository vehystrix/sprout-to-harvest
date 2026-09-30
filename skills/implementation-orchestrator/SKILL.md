---
name: implementation-orchestrator
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
- `persistent-workflow-state`: use for the run ledger, checkpoints, recovery
  states, and resume decisions.
- `git-isolated-implementation`: use before starting a Git-tracked run and when
  enforcing branch/commit policy.
- `subagent-recovery`: use whenever a delegated agent is interrupted or blocked.
- `requirements-traceability`: use to coordinate requirement, step, commit,
  validation, and documentation coverage.
- `agent-handoff`: use to validate every delegated agent's final handoff before consuming it.
- `model-catalog-format` and `model-routing-adapter`: use to freeze the effective
  catalog and policy, run the one-time capability probe, and resolve portable IDs.
- `run-ledger-format`, `plan-audit-format`, `chunk-index-format`,
  `requirements-inventory-format`, `step-context-format`,
  `step-status-format`, `checkpoint-format`,
  `documentation-context-format`, `documentation-assignment-format`, and
  `final-report-format`: use to create and validate the corresponding
  `.agent-work` artifacts.
- `verification-before-completion`: use before reporting any phase or run as complete.

## Rules
Keep the original plan immutable. Never load its body into orchestrator
context; pass only its path in every delegation, and delegate plan reading
to the roles that need the content.
- The orchestrator is the single authority for final model assignment selection.
  Agents may recommend models, but they cannot finalize or apply them.
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
   it and atomically write `run.yaml` using `run-ledger-format` with the inputs,
   `phase: initialization`, `status: pending`, `attempt: 0`, and the current
   timestamp before delegating. If it exists, read `run.yaml` using
   `run-ledger-format`, `chunk-index.yaml` using `chunk-index-format`, and the
   latest `reports/*.yaml` using `agent-handoff`; validate that the stored plan
   path, run directory, retry limit, and audit setting match the invocation.
   Resume the first non-completed phase or step selected by the
   persistent-state rules. Never overwrite a completed result.
2. **Confirm effective configuration and run the capability probe.** Load the
   effective catalog and policy (repository files, merged overrides confirmed
   as required), canonicalize both, copy them under `.agent-work/<run-id>/`,
   and calculate `sha256:` fingerprints. Run the capability probe exactly once
   per the `model-routing-adapter` skill; it determines whether the delegation
   tool surface accepts a per-delegation `model` parameter and pins the evidence
   channel. Persist `model_routing` in `run.yaml`: `catalog_source`, `policy_source`,
   `adapter` (active host identifier), `preflight: { status, mechanism, evidence_channel }`,
   fingerprints, and warnings including any routing-unavailable warning. If probe status is
   `routing-unavailable` and `require_application` is true, persist `blocked` and stop; otherwise
   continue - every later delegation omits the `model` field and records a
   routing-unavailable warning with `applied: false`.
3. **Prepare repository isolation.** Inspect Git before any file-modifying
   delegation. If Git exists, apply `git-isolated-implementation`, record the
   starting branch and commit, require clean tracked changes, and create or
   reuse the recorded implementation branch. If Git is unavailable, record the
   limitation and use `N/A` repository fields. If the required Git precondition
   fails, persist `blocked` and stop.
4. **Audit the plan.** Unless `Skip plan audit` is `true`, persist
   `phase: plan-audit`, `status: running`, and `attempt: 1`; delegate exactly once
   to `Plan Auditor` with only the plan path from `run.yaml`. Validate its handoff
   using `agent-handoff` and `plan-audit-format`, validate both Markdown context
   files using `documentation-context-format`, persist `plan-audit.yaml` from the
   handoff, record in run state the path of the `requirements-inventory.yaml` the
   auditor wrote itself per its report, then branch on its status:
   `NEEDS_CLARIFICATION` reports the required questions to the user and stops as
   `blocked`; `BLOCKED` reports the findings and stops as `blocked`. If audit is
   `plan-audit-format` with `status: SKIPPED`, the explicit user setting, and
   `documentation_context.status: UNAVAILABLE`; later documentation
   assignments must then be built from verified implementation evidence rather
   than a plan brief.
5. **Decompose and document the plan.** Persist `phase: decomposition`,
   `status: running`.
   Delegate exactly once to `Plan Decomposer` with only file paths - the plan
   from `run.yaml`, the persisted `plan-audit.yaml`, and - when the audit ran -
   `requirements-inventory.yaml`; when the audit was skipped, it derives the inventory
   itself. You pass the run's per-loop retry cap in that delegation; it owns the whole
   phase end to end. Accept only `PASS`. On return, validate using `chunk-index-format`:
   every step file exists and follows `step-context-format`, every inventory requirement is
   requirement is assigned to exactly one chunk, dependencies form an
   acyclic graph, every behavioral unit keeps its primary-test step
   immediately before its implementation step within its chunk, and
   every chunk's `doc_status` is `completed`. On any failed check,
   persist `blocked` and stop.
6. **Select the next step.** Read `chunk-index.yaml` using `chunk-index-format`
   and choose the first step in dependency order that is not `completed`. Do
   not select a step whose dependencies are not `completed`. If all steps are
   completed, continue to final verification. For a selected step, create or
   load `steps/<step-id>-status.yaml` using `step-status-format` and preserve
   its attempt count.
7. **Resolve the step assignment from the catalog.** Before each delegated
   call: (1) load the effective catalog and policy from `.agent-work/<run-id>/`;
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
	- Persist the step as `running` before delegating `Step Implementer`.
	- Pass only file paths: the step context, its latest checkpoint, and
	  the latest relevant verifier report; the delegated agent reads them.
	- Validate the implementer handoff. `PASS` may proceed to verification;
	  `RECOVERABLE` persists the recovery state and stops; `BLOCKED` persists the
	  blocker and stops. A missing or malformed handoff is `blocked` and does not
	  consume a retry.
	- Persist the step as `running` before delegating `Step Verifier`.
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
   once to `Final Verifier` with only file paths - the plan from `run.yaml`,
   `chunk-index.yaml`, every persisted handoff report, and the ledger's commit
   and repository state. `VERIFIED` continues; `INCOMPLETE` identifies the
   affected steps, consumes one final-verification repair attempt, and returns
   to step 8 within the retry limit; `BLOCKED` stops. Do not begin documentation
   until final verification is `VERIFIED`.
10. **Document source files.** When implementation is verified, build
    documentation assignments only for changed source files that require
    maintainer-facing documentation, using
    `documentation/source-documentation-context.md` from the plan audit as the
    initial brief. Refine the assignment with the final implementation,
    changed files, and relevant step reports; the implementation evidence is
    authoritative if it differs from the plan brief. For independent
    assignments, delegate `Documentation Writer` instances in parallel only
    when their files and ownership do not overlap; otherwise delegate
    sequentially. Persist each assignment before and after delegation. Require
    `PASS` plus a separate documentation commit, or `changed_files: []` with a
    material no-op explanation, or an explicit `N/A` Git explanation. A
    `RECOVERABLE` or `BLOCKED` result stops the documentation phase.
    Documentation assignments are selected only after final verification; they
    never inherit the decomposer step recommendations as final state.
11. **Verify source documentation.** Delegate `Documentation Verifier` for
    every completed source-documentation assignment. `VERIFIED` accepts the
    assignment; `INCOMPLETE` returns only that assignment to the documentation
    agent within the retry limit; `BLOCKED` stops. Do not request stylistic
    changes that are not material findings.
12. **Create and verify user documentation.** Create the user-documentation
    assignment from `documentation/user-documentation-context.md` referenced by
    `plan-audit.yaml`, adding the final implementation context, changed files,
    verified requirements, and repository-specific examples. Do not require the
    Documentation Writer to reread the complete plan when the Markdown brief and
    implementation context cover the assignment; the final implementation
    remains authoritative. Delegate `Documentation Writer`, then delegate
    `Documentation Verifier` with the paths of both files. Require
    `VERIFIED` before finalization; apply the same bounded retry rule and stop
    on `BLOCKED` or malformed handoffs.
13. **Finalize.** Run the final repository and validation checks. Build
    `final-report.yaml` using `final-report-format` from the ledger and all
    verified handoffs, including audit status, completed steps, commands and
    results, commits, traceability, branch/worktree state, documentation,
    warnings, and resume instructions. Atomically persist the final report
    before reporting completion. Completion is legal only when final
    verification and all required documentation verification are `VERIFIED`
    and the final repository check passes.
14. **Report directly to the user.** After persisting and validating
    `final-report.yaml`, report it using the user-facing response structure and
    status rules in `final-report-format`. The response must agree with the
    persisted report.

## Delegation contract

For every delegation, use this sequence exactly:

```text
persist phase/step as running
-> launch the named agent with only the listed context
-> receive exactly one agent-handoff/v1 report
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
Maintain `run.yaml`, `plan-audit.yaml`, `requirements-inventory.yaml`,
`chunk-index.yaml`, `steps/<step-id>.md`,
`steps/<step-id>-status.yaml`, `checkpoints/<step-id>.yaml`, `reports/*.yaml`,
documentation assignment Markdown files, commit hashes, and `final-report.yaml`.
Report completed work, validation evidence, blockers, and resume instructions using
`agent-handoff/v1`.

## Related agents

- Implementation Orchestrator (`agents/implementation-orchestrator.agent.md`)
- Plan Auditor (`agents/plan-auditor.agent.md`)
- Plan Decomposer (`agents/plan-decomposer.agent.md`)
- Step Implementer (`agents/step-implementer.agent.md`)
- Step Verifier (`agents/step-verifier.agent.md`)
- Final Verifier (`agents/final-verifier.agent.md`)
- Documentation Writer (`agents/documentation-writer.agent.md`)
- Documentation Verifier (`agents/documentation-verifier.agent.md`)
- Chunk Writer (`agents/chunk-writer.agent.md`)
- Chunk Verifier (`agents/chunk-verifier.agent.md`)
- Whole-Plan Verifier (`agents/whole-plan-verifier.agent.md`)
