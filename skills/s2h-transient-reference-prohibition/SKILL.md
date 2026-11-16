---
name: s2h-transient-reference-prohibition
description: Only use when explicitly invoked
# description: >-
#   Use whenever a subagent writes or verifies source code, tests, or committed
#   documentation; prohibits embedding transient workflow references in persistent files.
user-invocable: false
disable-model-invocation: true
---
# Transient Reference Prohibition

Persistent files - source code, test names and comments, and committed
documentation - MUST NOT reference anything that exists only for the duration of a run.
A name, comment, or sentence is transient when deleting every `.agent-work/` artifact,
plan, brief, report, and handoff would make it point at nothing.

MUST NOT embed in persistent files:

- Transient identifiers of any kind: requirement IDs (`REQ-012`), finding numbers
  (`F2`), chunk, step, task, run, attempt, ledger, or checkpoint IDs - in test names,
  symbols, comments, docstrings, or documentation prose.
- Process references that invoke the workflow instead of the product: "regression test
  for finding F2", "per the plan", "as required by REQ-012". Name the behavior, and
  describe a fix by its effect, not by the audit that found it.
- Transient design document names and paths - plans, requirements inventories, briefs,
  context files, handoff reports, run ledgers, `.agent-work/` locations - by name or
  paraphrase.

Persistent text refers only to product-domain concepts: behavior, interfaces, users,
inputs, errors, and invariants.

## Enforcement

- File-modifying subagents MUST scan the files they changed and created before committing;
  reword every match around product-domain terms. A stale transient reference in a file
  this step is already editing MUST be rewritten as part of that edit. Do not sweep
  unrelated files.
- Verification agents MUST apply the same scan to the files a step claims to have changed,
  and report each match as a finding with `missing_work`.
