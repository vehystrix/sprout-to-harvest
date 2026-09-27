---
name: systematic-debugging
description: Only use when explicitly invoked
# description: >-
#   Use when a test, validation command, subagent, or verifier reports an
#   unexpected failure or behavior.
user-invocable: false
disable-model-invocation: true
---
# Systematic Debugging

Reproduce the failure, capture the exact symptom, identify the smallest
controlling code path, and form one falsifiable root-cause hypothesis.
Run a focused check that could disconfirm it before editing.

Make the smallest repair in the same slice, rerun the same check, and
widen validation only after the local cause is resolved. Record unresolved
environmental blockers separately from code defects.
