---
name: step-context-format
description: "Defines the Markdown template and writing guidance for implementation step context files."
---
# Step Context Format

Use this skill when the decomposer creates `steps/<step-id>.md`.

## Frontmatter

The file begins with YAML frontmatter. It identifies the artifact; it does not contain the full step data.

```yaml
---
kind: step-context
schema: step-context/v1
run_id: run-001
step_id: step-001-implementation
type: implementation
---
```

## Template

```markdown
# Step: Implement the behavior

## Objective
State the one externally observable result this step must deliver. Keep it narrow enough for one commit.

## Requirements Covered
List exact requirement IDs and explain how this step contributes to each. Do not copy unrelated plan text.

## Dependencies
Name prerequisite step IDs and describe the artifact or behavior each prerequisite provides.

## Interfaces
Describe inputs, outputs, public names, file boundaries, and contracts this step consumes or produces. Include a small example when a value or protocol could be misunderstood.

## Likely Files
List the source and test paths that may change. This is an allowed-scope hint, not permission to edit unrelated files.

## Exact Scope
Describe the permitted implementation and the behavior that must remain unchanged. Call out important exclusions.

## Acceptance Criteria
Use observable, verifiable statements. Example: `When the manifest is missing, the loader returns BLOCKED and names the path.`

## Validation Commands
Give exact commands and expected outcomes. Include the focused test first and any broader check needed before commit.

## Expected Failure or Success
For a primary-test step, describe the intentional failing assertion. For an implementation step, describe the passing result. For non-behavioral work, explain why a failing test is not meaningful.

## Exclusions
List work that must not be done, such as unrelated cleanup, production changes in a test-only step, or weakening an assertion.

## Commit Expectations
State the required commit boundary and what evidence must be reported in the handoff.
```

## Writing guidance

Make the context self-contained: an implementer should not need to load the entire plan. Prefer concrete paths, commands, and examples over labels such as "handle errors". Every requirement and acceptance criterion must be testable, and every named interface must have one unambiguous meaning.
