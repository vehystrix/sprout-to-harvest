---
name: s2h-user-doc
description: Only use when explicitly invoked
# description: "Use when writing task-oriented docs for plan-driven implementations."
user-invocable: false
disable-model-invocation: true
---
# User Documentation

Document how users accomplish supported tasks, including prerequisites,
configuration, commands, expected results, examples, limitations, and
recovery guidance. Derive instructions from the implemented behavior and
public interfaces.

Prefer concise task flows over architecture narration. Verify commands and
examples against the repository before marking documentation complete.

Never mix maintainer-facing or code-level documentation into user-facing
files: per-function notes, invariants, and internal implementation details
belong inline with the code under `s2h-source-doc`. Architectural overview
material belongs in its own architecture documentation file, not in a README
or other user-facing document.
