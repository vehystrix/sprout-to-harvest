---
name: s2h-requirements-traceability
description: Only use when explicitly invoked
# description: "Accounts for every plan requirement across multi-step work."
user-invocable: false
disable-model-invocation: true
---
# Requirements Traceability

Use `s2h-handoff` for requirement and validation results exchanged between agents;
every result names its requirement, outcome, and concrete evidence.

Maintain a compact matrix linking:

```text
requirement -> primary-test step -> implementation step -> changed files
-> commit -> validation -> verification -> documentation
```

Every requirement must be `SATISFIED`, `PARTIAL`, `NOT_SATISFIED`,
`NOT_APPLICABLE`, or `BLOCKED`. Do not infer coverage from file names or test
counts.
Record the evidence and identify the next step for every non-success status.

Documentation cells are filled only once the documentation phase has run; before
then they MUST be recorded as pending and MUST NOT count against a verifier's
`DONE` result.

The final verifier uses this matrix as the basis for the completion decision,
evaluating every chain link except documentation; full chain completeness is
confirmed at finalization, when all required documentation verifications are
`DONE`.

## Related skills

- `s2h-handoff`
