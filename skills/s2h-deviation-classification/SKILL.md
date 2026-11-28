---
name: s2h-deviation-classification
description: Only use when explicitly invoked
# description: "Defines how a validating delegator classifies a saved handoff
#   that deviates from the exact s2h-handoff schema."
user-invocable: false
disable-model-invocation: true
---
# Deviation Classification

Use this skill whenever you validate a delegated agent's saved handoff against
`s2h-handoff`.

A final message that reports an unsupported status is handled by this rule; the
saved report file, never the message text, decides classification. A handoff that
deviates from the exact `s2h-handoff` schema - including status vocabulary (for
example, `COMPLETED` where `DONE` is required) and field naming - MUST be classified
before use. Classify in this order:

1. If the deviating value maps one-to-one onto a valid `s2h-handoff` outcome and
   the saved handoff's own details and evidence substantiate that outcome without
   contradicting its repository fields, derive it directly from the saved handoff;
   record `derived_fields` with a warning naming each derived field. For example,
   status `COMPLETED` maps to `DONE`, and validation result `FAIL (intended)` or
   `PASS (green pre-existing)` maps to `FAIL` or `PASS`. You MUST NOT re-run
   validations or tests to re-derive an outcome the handoff already substantiates.
2. Only when no such one-to-one mapping holds, or the handoff's own evidence does
   not substantiate the outcome, derive it from ground truth (repository state,
   step status, run ledger); record `derived_fields` with a warning naming each
   derived field, leaving the handoff untouched.
3. Otherwise it is `blocked`, with the deviation described and the exact resume
   action recorded. A delegator MUST NOT normalize, edit, reinterpret, or
   automatically retry a deviating handoff; resumption re-delegates that one
   delegation on a later invocation, and persisted checkpoints mean no completed
   work is redone.

## Related skills

- `s2h-handoff`: the schema and authoring requirements this rule classifies
  deviations from; its Rules bind writers only.
