---
name: s2h-doc-context-format
description: Only use when explicitly invoked
# description: "Defines the Markdown templates for plan-level source and user documentation context."
user-invocable: false
disable-model-invocation: true
---
# Documentation Context Format

Use this skill when the `s2h-PlanAuditor` creates the plan-level
documentation context under `.agent-work/<run-id>/documentation/`.

The context is a flexible Markdown brief distilled from the immutable
plan. It identifies documentation obligations without claiming that
planned behavior was implemented. The final implementation and verified
repository state are authoritative when they differ from this brief.

## Source Documentation Context

Persist as `documentation/source-doc-context.md`:

```markdown
---
kind: documentation-context
schema: documentation-context/v1
run_id: run-001
context_type: source
---

# Source Documentation Context

## Purpose
Explain what maintainers or API consumers need to understand about the planned change.

## Audiences
- Maintainers
- API consumers

## Requirements
- REQ-001: Describe the behavior that may require source documentation.
If no obligation applies, write exactly one bullet: - none: <one-line reason>.


## Topics
- Public interfaces
- Invariants
- Error contracts

## Interfaces and Constraints
Describe planned public names, inputs, outputs, dependencies, and compatibility constraints.

## Risks and Questions
Record documentation risks, migration concerns, and unresolved documentation questions.

## Expected Evidence
List implementation files, tests, commands, or examples that should establish the final facts.
```

## User Documentation Context

Persist as `documentation/user-doc-context.md`:

```markdown
---
kind: documentation-context
schema: documentation-context/v1
run_id: run-001
context_type: user
---

# User Documentation Context

## Purpose
Explain what users must be able to accomplish after the planned change.

## Audiences
- End users

## Requirements
- REQ-001: Describe the user-visible behavior that may require documentation.
If no obligation applies, write exactly one bullet: - none: <one-line reason>.


## Workflows
- Name the workflow users need to follow.

## Prerequisites and Configuration
List prerequisites, configuration, permissions, environment assumptions, and setup steps.

## Examples and Expected Results
List commands, inputs, outputs, examples, and success indicators that
the final documentation should contain.

## Limitations and Recovery
Record planned limitations, failure modes, troubleshooting, migration, or recovery guidance.

## Risks and Questions
Record documentation risks and unresolved questions without inventing answers.

## Expected Evidence
List implementation files, tests, commands, or examples that should establish the final facts.
```

## Validation

The frontmatter MUST be flat scalar key-value lines; quoted values are
supported, and folded or multi-line values, list items, flow collections,
and comments produce a named FAIL naming the offending key. Require `kind`,
`schema`, `run_id`, and a `context_type` of source or user; `kind` is
"documentation-context" and `schema` is "documentation-context/v1".

The H1 title MUST equal the fixed title for that type, and every template
heading for that type MUST be present. The `## Requirements` section MUST
contain at least one bullet with a non-empty description; if no documentation
obligation was identified, write exactly one bullet in the fixed form
`- none: <one-line reason>`. Prose alone is not enough - id-bearing prose with
no bullets still fails.

No claim may be supported only by the plan when implementation evidence is
available; that content rule stays with s2h-DocumentationVerifier, not this
script.

The rules above are enforced by `scripts/validate.py <file> [files...]`, which
exits 0 only on pass; the script enforces these rules but never defines them.
Before persisting a documentation context file: MUST run the validator and the
file MUST pass validation before persistence.
