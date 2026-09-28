---
name: plan-decomposition
description: >-
  Use when splitting an approved implementation plan into small, ordered work units
  with per-chunk verification.
disable-model-invocation: true
---
# Plan Decomposition

Two invocation modes share one pipeline; only the persistence differs.

- Delegated mode (orchestrator or a role agent delegates): persist exactly
  what `persistent-workflow-state`, `step-index-format`, and
  `agent-handoff` require in `.agent-work/<run-id>/`. The orchestrator owns
  loop control, retry accounting, and `doc_status` persistence; this skill
  describes the roles it composes.
- User-invoked mode (invoked directly by a user outside an orchestrated
  run): required inputs are the plan and an Output directory, plus an
  optional per-chunk repair-limit default of three. If any input is missing
  or unusable, `BLOCK` and ask; never fall back to `.agent-work/`. The
  deliverable is the implementation step files written directly under the
  Output directory - no nested `steps/` subdirectory; the set of files IS the
  deliverable. No workflow state is persisted: no run.yaml, checkpoints,
  counters, or index. Communication artifacts live in `<output-dir>/.work/`.

## Chunking

Decompose the plan into chunks by behavioral units, not file paths. Each
chunk owns an end-state and a contract:

- `requirements_assigned`: requirement IDs from the plan's inventory that
  this chunk covers. Every inventory requirement must be assigned to
  exactly one owning chunk; cross-cutting requirements split into
  `<parent-id><suffix>` sub-requirements, each owned by one chunk.
- `requirement_excerpts`: verbatim plan text for every assigned ID.
- `interfaces_in` / `interfaces_out`: names and signatures of what the
  chunk consumes from or produces for other chunks.
- `end_state`: one paragraph on what exists when the chunk completes.
- `exclusions`: work the chunk must not do.

Chunks carry no topological order requirement; they may be processed in
parallel. Step files within a chunk keep test-first ordering per
`test-first-plan-steps`.

## Per-chunk documentation loop

For each chunk, run a writer-verifier pair:

1. **Step Documentation Writer** receives the full plan (fidelity context),
   the chunk contract with verbatim excerpts, boundary contracts of adjacent
   chunks, and - on repair rounds only - the prior verifier findings. It
   creates or updates `steps/<step-id>.md` files per `step-context-format`,
   embedding the contract verbatim in every file of its chunk. It checks
   intra-chunk completeness: every assigned requirement appears in at least
   one step, and every claim traces to a contract excerpt (drift check).
2. **Step Documentation Verifier** is read-only and confirms documentary
   traceability for every material requirement in the chunk; it never edits
   files. It returns `VERIFIED`, `INCOMPLETE` with structured findings
   (`{id, requirement ref, one-line description}`), or `BLOCKED`.

Repair loop: an `INCOMPLETE` consumes one of the per-chunk retry limit (the
count of repairs after the initial writer pass; default three in user mode).
A `BLOCKED` or malformed handoff never consumes a retry. When retries are
exhausted, stop and flag the chunk to the user with its findings, current
file state, and options.

## Whole-plan verification pass

After all chunks verify, run the **Whole-Plan Verifier** read-only against
the full plan and the complete requirement-assignment inventory. It performs
only global checks no single chunk can see: unassigned content (a chunk
cannot tell "uncovered" from "covered by another chunk"), duplicate
ownership, and boundary consistency between chunks.

Findings route by classification; only affected chunks rerun - unchanged chunks keep
their `VERIFIED` status:

- `decomposition-gap`: re-delegate Step Decomposer with the report, adjust only
  affected chunks, then rerun those chunk loops.
- `boundary-mismatch`: send the findings to the affected chunks' writers, rerun
  them, and reverify those chunks.

The whole-plan pass reruns until clean. The retry limit is shared across all
outer iterations of this pipeline; exhaustion blocks the run and flags the
user with the chunk-level evidence collected so far.

If the plan is too large to fit one context, writers work from their chunk
contract plus verbatim excerpts alone; loss detection then lives entirely in
the whole-plan pass, which reads the full plan in windows against the
inventory.

## Direct-invocation protocol (user mode)

Communication with subagents uses fixed `agent-handoff/v1` documents in both
modes. The parent reads only status and findings headers from each
handoff; full bodies stay in `<output-dir>/.work/`. Fixed input template:

```markdown
Role: <step-documentation-writer | step-documentation-verifier | whole-plan-verifier | step-decomposer>
Task ID and attempt: <chunk-id>, attempt <n>
Plan: <full plan path or inline text>
Contract: <chunk contract with verbatim requirement excerpts>
Assigned requirements: <IDs + verbatim excerpts>
Prior verification report: <findings, repair rounds only; omit on first pass>
```

`.work/` contents: writer handoffs, verifier findings, and decomposer
repair notes, each named with chunk ID plus attempt. Nothing is deleted
automatically: after success the parent reports `.work/` as safe to delete
after inspection; a blocked run keeps it as blocker evidence; deletion is
explicit user action only.

Resume is reports-as-state: re-invoking the same plan and Output directory
skips chunks that already have their step files plus a `VERIFIED` report in
`.work/`; decomposer repairs invalidate affected chunks by deleting their
step files and reports so they regenerate.

## Blocked conditions

- Missing, empty, or non-Markdown plan input: `BLOCK` with the evidence.
- Requirement inventory missing from the plan or a requirement cannot be
  assigned to any chunk: `BLOCK`.
- Chunk contract missing, contradictory, or referencing dependencies that do
  not exist in the plan: writer `BLOCK`s before writing.
- Retry exhaustion on any chunk after repairs: `BLOCK` with findings and file
  state; flag the user.

## Related skills

- `step-context-format`
- `test-first-plan-steps`
- `requirements-traceability`
- `agent-handoff`
- `persistent-workflow-state`