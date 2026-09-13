---
name: documentation-assignment-format
description: "Defines the Markdown template and guidance for persisted documentation assignments."
---
# Documentation Assignment Format

Use this skill when the orchestrator creates or a Documentation Agent reads `documentation/<assignment-id>.md`.

## Frontmatter

```yaml
---
kind: documentation-assignment
schema: documentation-assignment/v1
run_id: run-001
assignment_id: source-api-loader
assignment_type: source | user
---
```

## Template

```markdown
# Documentation Assignment: Describe the target

## Scope
Identify the exact source file, documentation page, or documentation set to update. Explain the audience and why the assignment exists.

## Requirements
List requirement IDs and the externally visible behavior that must be documented. Include configuration or prerequisite details when users need them.

## Plan Documentation Context
Copy the relevant Markdown context from the path referenced by `plan-audit.yaml`, using `documentation-context-format`. Treat it as the plan-level documentation brief: use its audiences, topics, requirements, and risks to scope the assignment, then reconcile it with the verified implementation. Do not treat planned behavior as implemented behavior.

## Source and Context Paths
List the implementation, Markdown documentation context, plan requirements, interfaces, and prior reports that establish the facts. Explain what each path contributes. The assignment should provide enough context that the Documentation Agent does not need to reread the complete plan.

## Acceptance Criteria
State the material facts, examples, commands, links, and limitations that must be correct. Example: `The page shows the exact CLI invocation and the expected successful output.`

## Exclusions
List files and concerns outside this assignment. Do not turn a documentation assignment into an implementation refactor.
```

Write factual, audience-specific guidance. Source assignments explain contracts and invariants maintainers or consumers rely on; user assignments explain workflows and expected outcomes. Include a small command or usage example when prose alone could leave invocation details ambiguous. Do not persist assignments as YAML or extensionless text.
