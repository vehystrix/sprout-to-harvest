---
name: documentation-context-format
description: "Defines the Markdown templates for plan-level source and user documentation context."
---
# Documentation Context Format

Use this skill when the Plan Auditor creates or the orchestrator reads the plan-level documentation context under `.agent-work/<run-id>/documentation/`.

The context is a flexible Markdown brief distilled from the immutable plan. It identifies documentation obligations without claiming that planned behavior was implemented. The final implementation and verified repository state are authoritative when they differ from this brief.

## Source Documentation Context

Persist as `documentation/source-documentation-context.md`:

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

Persist as `documentation/user-documentation-context.md`:

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

## Workflows
- Name the workflow users need to follow.

## Prerequisites and Configuration
List prerequisites, configuration, permissions, environment assumptions, and setup steps.

## Examples and Expected Results
List commands, inputs, outputs, examples, and success indicators that the final documentation should contain.

## Limitations and Recovery
Record planned limitations, failure modes, troubleshooting, migration, or recovery guidance.

## Risks and Questions
Record documentation risks and unresolved questions without inventing answers.

## Expected Evidence
List implementation files, tests, commands, or examples that should establish the final facts.
```

## Validation

Require YAML frontmatter with `kind`, `schema`, `run_id`, and the correct `context_type`. Require every template heading, at least one requirement or an explicit statement that no documentation obligation was identified, and no claim that is supported only by the plan when implementation evidence is available.
