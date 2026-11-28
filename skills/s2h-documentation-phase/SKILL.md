---
name: s2h-documentation-phase
description: Only use when explicitly invoked
# description: "Documentation phase contract for the s2h-DocumentationPhase tier."
user-invocable: false
disable-model-invocation: true
---
# Documentation Phase

The documentation phase of one run begins only after final verification is DONE. It
builds source-doc assignments for changed files requiring maintainer-facing
documentation, runs a bounded writer-verifier cycle per assignment, and creates
and verifies the user-doc assignment last.

## Input

Input is the run directory, the final changed files from the ledger, and the
paths of `documentation/source-doc-context.md` and `documentation/user-doc-context.md`.

## Source-doc assignments

1. Build a source-doc assignment per `s2h-doc-assignment-format` only for each
   changed file requiring maintainer-facing documentation; assignments never
   inherit decomposer step recommendations as final state. Refine each with the
   final changed files and relevant step reports; when implementation evidence
   differs from the plan brief, the implementation evidence is authoritative.
   Persist every assignment before and after delegation.
2. Resolve each writer model per Model resolution below; append a delegation
   line to `delegations.jsonl` before each spawn. Delegate `s2h-DocumentationWriter`
   instances in parallel only when their files and ownership do not overlap, else
   sequentially, using the verbatim source-doc block below. Require `DONE` plus a
   separate documentation commit, or `changed_files: []` with a material no-op
   explanation, or an explicit `N/A` Git explanation.
3. On writer `INCOMPLETE`, return only that assignment to its writer within cap
   L - at most L after its initial attempt, counters fresh per assignment -
   including the named findings; when the allowance is consumed, stop as BLOCKED
   naming the assignment and "retries exhausted". A writer `BLOCKED` stops the
   phase as BLOCKED without consuming a retry.
4. For every completed source-doc assignment, delegate `s2h-DocumentationVerifier`
   using the verbatim block below with the assignment's Markdown context file and
   the documented file path(s); resolve its model per Model resolution and append
   its delegation line. On `DONE`, accept the assignment; on `INCOMPLETE`, return
   only that assignment to its writer within cap L and reverify before accepting.
   Do not request stylistic changes that are not material findings.
5. Validate every writer and verifier handoff against `s2h-handoff` before
   consuming it; a summary pointing at a missing or unreadable report is BLOCKED
   with the raw failure description as resume action, never reinterpretation.

## User-doc assignment (last)

Create the user-doc assignment last per `s2h-doc-assignment-format`; its content
draws on `documentation/user-doc-context.md` referenced by `s2h-plan-audit.json`,
the final verified requirements from `requirements.json`, and repository-specific
examples; do not require the writer to reread the complete plan when the Markdown
brief and implementation context cover it - the final implementation remains
authoritative. Delegate
`s2h-DocumentationWriter` using the verbatim user-doc block, then delegate
`s2h-DocumentationVerifier` with both files' paths. Require `DONE` before phase
completion; apply the same bounded retry rule and stop on `BLOCKED` or malformed
handoffs.

## Model resolution

Resolve each delegated role (`doc-writer`, `doc-verifier`) at delegation time per
`s2h-model-routing-adapter`. Read the frozen run copies of catalog and policy
under the run directory and the probe status from
`run.json.model_routing.preflight.status`; on resume, confirm their fingerprints
are unchanged before use. Evaluate the role's policy `required_capabilities`
and `minimum_tier`, then select a portable ID: the role's policy default when no
recommendation applies; record the selection source. Resolve the host mapping
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

**s2h-DocumentationWriter, source-doc assignment** (one per changed file)

```text
Role: s2h-DocumentationWriter
Task ID and attempt: source-doc/<changed-file>, attempt <n>
Paths:
  - Run directory: <run-dir>
  - Documentation context: <run-dir>/documentation/source-doc-context.md
  - Final changed files (one bullet per file):
    - <changed-file-path-1>
    - <changed-file-path-2>
  - Relevant step reports (one bullet per report):
    - <step-report-path-1>
    - <step-report-path-2>
Duties:
  - make a separate documentation commit before returning
Constraint:
  - file-modifying; edit only the assigned documentation set
  - MUST read the `AGENTS.md` at the repository root, plus any `AGENTS.md` in a
    subdirectory of that repo containing the files your work targets; if none exist,
    proceed without one; apply everything that is relevant to your work
```

**s2h-DocumentationVerifier** (one per assignment)

```text
Role: s2h-DocumentationVerifier
Task ID and attempt: doc-verify/<assignment-id>, attempt <n>
Paths:
  - Run directory: <run-dir>
  - Assignment brief: the assignment's Markdown context file
  - Written documentation: the documented file path(s)
Constraint:
  - read-only
  - MUST read the `AGENTS.md` at the repository root, plus any `AGENTS.md` in a
    subdirectory of that repo containing the files your work targets; if none exist,
    proceed without one; apply everything that is relevant to your work
```

**s2h-DocumentationWriter, user-doc assignment**

```text
Role: s2h-DocumentationWriter
Task ID and attempt: user-doc, attempt <n>
Paths:
  - Run directory: <run-dir>
  - Documentation context: <run-dir>/documentation/user-doc-context.md
  - Final verified requirements: <run-dir>/requirements.json
Duties:
  - make a separate documentation commit before returning
Constraint:
  - file-modifying
  - MUST read the `AGENTS.md` at the repository root, plus any `AGENTS.md` in a
    subdirectory of that repo containing the files your work targets; if none exist,
    proceed without one; apply everything that is relevant to your work
```

Placeholders: `<run-dir>` is the run directory; `<assignment-id>` names the
assignment; `<n>` is the 1-based attempt number of the delegation from persistent
state. After any compaction or resume, MUST re-read this skill before delegating
again; patterns remembered from earlier in the session do not supersede the
verbatim templates above.

## Bounded summary and blocked semantics

Report one fixed-size result: `status` plus the saved report path; on BLOCKED add
its exact resume action. No narrative text, no repetition of acceptance criteria.
Never auto-redelegate a BLOCKED task; no BLOCKED consumes a repair attempt; an
exhausted assignment becomes BLOCKED naming "retries exhausted".

## Related skills

- `s2h-compaction-recovery`: MUST invoke at session start and re-read after every compaction.
- `s2h-persistent-state`: MUST use for resume decisions and the atomic write rule.
- `s2h-model-routing-adapter`: MUST use to resolve each delegated role's model
  at delegation time, including host mapping lookup and fallback order.
- `s2h-run-ledger-format`: MUST use for the `delegations.jsonl` line format and its validator.
- `s2h-doc-assignment-format`: MUST use to build and persist every assignment.
- `s2h-handoff`: MUST use to validate every delegated handoff before consuming it.
