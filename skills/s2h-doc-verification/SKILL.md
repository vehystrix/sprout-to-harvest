---
name: s2h-doc-verification
description: Only use when explicitly invoked
# description: "Use when updating or reviewing documentation after a plan-driven implementation."
user-invocable: false
disable-model-invocation: true
---
# Documentation Verification

Document behavior that users or maintainers need to rely on:
public interfaces, configuration, error contracts, invariants,
workflows, prerequisites, examples, and limitations.

Verify documentation against the plan and current implementation.
Flag only material omissions, contradictions, invalid examples,
missing prerequisites, or major clarity problems.
Do not turn verification into copy editing.

Keep source documentation close to the interface it describes.
Keep user documentation task-oriented and separate from internal implementation details.

Flag audience mixing between maintainer-facing and user-facing documents,
per-function documentation that is not inline with the code it describes,
and architectural overview material placed in a user-facing file such as
a README or inside function-level documentation.
