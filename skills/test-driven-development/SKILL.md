---
name: test-driven-development
description: "Use when implementing or changing observable behavior, before writing production implementation code."
---
# Test-Driven Development

Write the primary test for the intended external behavior first. Run it
and confirm it fails for the expected missing behavior rather than a
test setup error. Implement the smallest change that makes it pass, then
add only justified edge-case or regression tests.

Keep primary tests distinguishable from supplementary tests so the plan
can verify that the required behavior was specified before
implementation.
