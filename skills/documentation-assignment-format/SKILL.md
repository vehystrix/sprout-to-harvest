---
name: documentation-assignment-format
description: Only use when explicitly invoked
# description: "Defines the persisted documentation assignment template and guidance."
user-invocable: false
disable-model-invocation: true
---
# Documentation Assignment Format

Use this skill when the orchestrator creates `documentation/<assignment-id>.md`.

## Frontmatter

```yaml
---
kind: documentation-assignment
schema: documentation-assignment/v1
run_id: run-001
assignment_id: source-api-loader
assignment_type: source | user
model_assignments:
  writer:
    portable_id: documentation-standard
  verifier:
    portable_id: reasoning-pro
---
```

The YAML frontmatter includes independent writer and verifier model
assignments per the rules below.

Validation rules:

- `model_assignments.writer.portable_id` and `model_assignments.verifier.portable_id` are required.
- Writer and verifier assignments must be
independent; a verifier may use a stronger model than
the writer, but it cannot be a duplicate of the same
assignment without a policy rationale.
- The writer assignment is created only after
implementation evidence is available and verified.
- The Markdown body must contain only the
documentation brief, scope, acceptance criteria,
and instructions; it must not restate model
evidence or runtime selection details.

## Template

```markdown
# Documentation Assignment: Describe the target

## Scope
Identify the exact source file, documentation
page, or documentation set to update. Explain the
audience and why the assignment exists.

## Requirements
List requirement IDs and the externally visible
behavior that must be documented. Include
configuration or prerequisite details when
users need them.

## Plan Documentation Context
Copy the relevant Markdown context from the path referenced by `plan-audit.yaml`, using
`documentation-context-format`. Treat it as the plan-level documentation brief: use its
audiences, topics, requirements, and risks to scope the assignment; reconcile against
the verified implementation.

## Source and Context Paths
List the implementation, Markdown
documentation context, plan requirements,
interfaces, and prior reports that establish
the facts. Explain what each path contributes.
The assignment should provide enough context
that the Documentation Writer does not need to
reread the complete plan.

## Acceptance Criteria
State the material facts, examples, commands,
links, and limitations that must be correct.
Example:
`The page shows the exact CLI invocation and the expected successful output.`

## Exclusions
List files and concerns outside this
assignment. Do not turn a documentation
assignment into an implementation refactor.
```

Write factual, audience-specific guidance.
Source assignments explain contracts and
invariants maintainers or consumers rely on;
user assignments explain workflows and
expected outcomes. Include a small command
or usage example when prose alone could leave
invocation details ambiguous. Do not persist
assignments as YAML or extensionless text.

## Validation

Require YAML frontmatter with `kind`, `schema`, `run_id`, `assignment_id`, `assignment_type`,
and the complete `model_assignments` block; validate everything else per the rules above.
