---
name: s2h-source-doc
description: Only use when explicitly invoked
# description: "Use when documenting public interfaces, invariants, error contracts,
# or non-obvious behavior in affected source files."
user-invocable: false
disable-model-invocation: true
---
# Source Documentation

Document what maintainers and consumers must rely on: public inputs and
outputs, side effects, invariants, failure behavior, lifecycle constraints,
and non-obvious tradeoffs.

Keep documentation close to the interface, avoid narrating obvious code,
and do not change behavior or perform unrelated prose cleanup.

Per-function and per-interface documentation MUST be inline comments or
docstrings next to the code it describes; it does not belong in separate
documentation files. Architectural overview material belongs in its own
architecture documentation file, never in user-facing files such as a
README. Do not mix in user-facing content: task flows, setup steps, and
usage guidance are covered by `s2h-user-doc`.
