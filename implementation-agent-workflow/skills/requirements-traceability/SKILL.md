---
name: requirements-traceability
description: "Use when planning, verifying, or documenting multi-step work where every plan requirement must be accounted for."
---
# Requirements Traceability

Use `agent-handoff` for requirement and validation results exchanged between agents. Every result must identify the requirement, outcome, and concrete evidence; missing evidence is not coverage.

Maintain a compact matrix linking:

```text
requirement -> primary-test step -> implementation step -> changed files -> commit -> validation -> verification -> documentation
```

Every requirement must be `satisfied`, `partially-satisfied`, `not-satisfied`, or `blocked`. Do not infer coverage from file names or test counts. Record the evidence and identify the next step for every non-success status.

The final verifier uses this matrix as the basis for the completion decision.
