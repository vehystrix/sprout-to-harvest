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
before use: when the outcome is derivable from ground truth (repository state, step
status, run ledger), or when the saved handoff's own details and evidence substantiate
the outcome without contradicting its repository fields, derive the delegation's
ledger entry with `derived_fields` plus a warning naming each derived field, leaving
the handoff untouched; otherwise it is `blocked`, with the deviation described and
the exact resume action recorded. A delegator MUST NOT normalize, edit, reinterpret,
or automatically retry a deviating handoff. Resumption re-delegates that one
delegation on a later invocation, and persisted checkpoints mean no completed work
is redone.

## Related skills

- `s2h-handoff`: the schema and authoring requirements this rule classifies
  deviations from; its Rules bind writers only.
