---
name: s2h-plan-decomposition
description: >-
  Decompose implementation plans into independently implementable
  chunks with documented steps and delegated documentation loops.
user-invocable: true
disable-model-invocation: true
argument-hint: <plan-text-or-path> [<output-dir>]
---

Use this skill to turn an approved implementation plan into a run of
decomposed, chunk-level work items. The Plan Decomposer owns the whole
decomposition phase for one run: it consumes or derives the requirements
inventory, writes `chunk-index.yaml`, runs each chunk's Chunk Writer and
Chunk Verifier loop, and delegates the Whole-Plan Verifier pass.

## Requirements inventory

The inventory is always its own file, shaped by `s2h-requirements-format`:
one entry per requirement with an `id`, a short `name`, and a verbatim plan
`excerpt`. The Plan Decomposer consumes it or derives it:

- Delegated mode - consume: the Plan Auditor has already written
  `.agent-work/<run-id>/requirements.yaml` itself on a `PASS` audit,
  recorded in its handoff as `details.requirements_path`. Read it; never re-derive.
- User mode, or any run where auditing is absent or skipped - derive: extract
  every material requirement from the plan (explicit and implied), split
  cross-cutting ones into `<parent-id><suffix>` sub-requirements so each final ID
  fits one chunk, and write `<output-dir>/.work/requirements.yaml`
  with `source: plan-decomposer`. In delegated mode a derived inventory goes
  to `.agent-work/<run-id>/requirements.yaml` with the same source.

Coverage is a real check, not an assertion. When you write the chunk index,
verify that every inventory requirement appears in exactly one chunk's
`requirements_assigned` list and each assigned ID resolves into the file. The
Whole-Plan Verifier repeats this check independently against the full plan; its
second pass catches drift the first one missed.

## Chunking rules

Chunk the plan into independently implementable units of work:

- A `behavioral` chunk carries exactly two steps - a `primary-test` step
  immediately before its dependent `implementation` step, with the test named in
  the implementation's `dependencies`.
- A `non-behavioral` chunk (build wiring, configuration, scaffolding with no
  behavior to verify) carries exactly one step of type `non-behavioral`.
- Every step belongs to exactly one chunk; every inventory requirement is
  assigned to exactly one chunk.
- Contracts never live in the index. They live verbatim only in each chunk's
  step files per `s2h-step-context-format`, sourced from the inventory excerpts, so
  a Chunk Writer receives its contract directly and a verifier can check it line
  by line against the plan text.

`chunk-index.yaml`, shaped by `s2h-chunk-index-format`, is the machine state: one
entry per chunk with its `requirements_assigned` IDs, `doc_status`, step list,
and model blocks for all four roles. The Plan Decomposer initializes every
`doc_status` to `pending` when it writes the index and persists status changes
as the loops run.

## Per-chunk documentation loop

For each chunk in dependency order:

1. Persist `doc_status: running`.
2. Delegate to a Chunk Writer with only file paths - the plan, `chunk-index.yaml`,
   and `requirements.yaml`, from which the chunk's contract resolves; on
   repair rounds include the prior findings - using the persisted
   documentation-loop model assignments. The writer is this chunk's architect: it
   derives implementation detail into the step files, so missing detail is its
   normal job, not a defect.
3. On a writer `PASS` or `RECOVERABLE`, delegate to a Chunk Verifier with the
   same template minus findings; on a writer `BLOCKED`, record the blocker and
   move on to the next chunk.
4. On an `INCOMPLETE` verdict, persist `doc_status: verification-failed`,
   re-delegate the writer with the named findings, and repeat while this loop
   instance has repair attempts left - at most `L` after its first attempt, where
   `L` is the run's configured retry limit passed by the orchestrator; counters
   are fresh for every new loop instance.
5. Only on a `VERIFIED` verdict, persist `doc_status: completed`.

A loop instance that exhausts its allowance is not retried again; its blocker
becomes one of the blocked conditions below.

## Model assignments

Resolve the documentation-loop roles (`chunk-writer`, `chunk-verifier`) through
the catalog routing path at delegation time, and persist each assignment into
the index with its timestamp and `source: decomposer`; a null recommendation stays
explicit in `model_recommendations` even when an assignment is persisted. The
Whole-Plan Verifier's model assignment goes only in that delegation's handoff
details, never in the index.

## Whole-plan pass

When every chunk has `doc_status: completed`, delegate to a Whole-Plan Verifier
with only file paths - the plan, `requirements.yaml`, and
`chunk-index.yaml`. It re-checks coverage against the full plan text and
boundary fidelity across chunks, reading each chunk's Contracts from its step files.
Route each finding to the actor that owns the artifact the defect lives in: a
finding that requires changing `requirements_assigned` or chunk boundaries is a
decomposition-gap; any other finding is a boundary-mismatch.

- A decomposition-gap is repaired directly by you - rewrite the affected chunks'
  `requirements_assigned`, and the inventory too when the gap reveals a derivation
  miss, then rerun those chunks' writer and verifier loops as fresh loop instances
  under the same `L` allowance, persisting `doc_status: verification-failed` per
  affected chunk.
- A boundary-mismatch is repaired by re-delegating the affected chunk writer(s) with
  the findings; each repair starts a fresh loop instance with the same `L` allowance,
  and rerun that chunk's verifier before completing it again.
- Whole-plan verifications total at most `L + 1` per run - one initial pass plus up
  to `L` re-verifications after repair rounds. A finding on the `(L+2)`nd pass
  returns `BLOCKED`.
- An infrastructure failure (unreadable files, missing handoff) escalates: the
  phase returns `BLOCKED`.

## User-mode run directory

In user mode the Plan Decomposer writes directly into `<output-dir>/.work/`:
`requirements.yaml` when it derived one, `chunk-index.yaml`, and one
context file plus status file per step under `.work/steps/`. Delegation roles in
user mode are limited to `chunk-writer`, `chunk-verifier`, `whole-plan-verifier`,
and `plan-decomposer`.

## Blocked conditions

Return `BLOCKED` when:

- The plan yields no derivable material requirements, or is unparseable enough
  that an inventory cannot be built;
- A loop instance is blocked past its allowance - writer `BLOCKED`, verifier
  `BLOCKED`, or repeated `INCOMPLETE`;
- Whole-plan findings reveal a contract-level defect that re-delegation within
  the per-loop allowances cannot fix, including findings on the `(L+2)`nd pass.

Every other failure mode is repairable inside the loops above; do not escalate it.
