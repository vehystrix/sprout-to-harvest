---
name: step-context-format
description: Only use when explicitly invoked
# description: "Defines the Markdown template and writing guidance for
# implementation step context files."
user-invocable: false
disable-model-invocation: true
---
# Step Context Format

Use this skill when defining a chunk contract, and when step-documentation
writers create or verifiers validate `steps/<step-id>.md`.

## Frontmatter

The file begins with YAML frontmatter.
It identifies the artifact; it does not contain the full step data.

```yaml
---
kind: step-context
schema: step-context/v1
run_id: run-001
step_id: step-001-implementation
chunk_id: chunk-001
type: implementation
---
```

## Template

```markdown
# Step: Implement the behavior
## Contract
State this step's chunk contract, verbatim in every step file of the
chunk:
- Chunk ID and one-paragraph deliverable end-state: what exists when the
  chunk completes.
- Assigned requirement IDs with their verbatim plan excerpts - the exact
  plan text this chunk must cover.
- Interfaces in/out: names, signatures, and values this chunk consumes from
  or produces for other chunks.
- Exclusions summary: work the chunk must not do.

## Objective
State the one externally observable result this step must deliver.
Keep it narrow enough for one commit.

## Requirements Covered
List exact requirement IDs and explain how this step contributes to each.
Do not copy unrelated plan text.

## Dependencies
Name prerequisite step IDs and describe the artifact or behavior each prerequisite provides.

## Interfaces
Describe inputs, outputs, public names, file boundaries, and
contracts this step consumes or produces. Include a small example
when a value or protocol could be misunderstood.

## Likely Files
List the source and test paths that may change. This is an
allowed-scope hint, not permission to edit unrelated files.

## Exact Scope
Describe the permitted implementation and the behavior that must
remain unchanged. Call out important exclusions.

## Acceptance Criteria
Use observable, verifiable statements. Example:
`When the manifest is missing, the loader returns BLOCKED and names the path.`

## Validation Commands
Give exact commands and expected outcomes. Include the focused
test first and any broader check needed before commit.

## Expected Failure or Success
For a primary-test step, describe the intentional failing
assertion. For an implementation step, describe the passing
result. For non-behavioral work, explain why a failing test is
not meaningful.

## Exclusions
List work that must not be done, such as unrelated cleanup,
production changes in a test-only step, or weakening an assertion.

## Commit Expectations
State the required commit boundary and what evidence must be reported in the handoff.
```

## Writing guidance

Make the context self-contained: an implementer should not need to load the entire plan.
Prefer concrete paths, commands, and examples over labels such as "handle errors".
Every requirement and acceptance criterion must be testable,
and every named interface must have one unambiguous meaning.
Every claim in a file must trace to a Contract requirement excerpt or field;
a claim without such a trace is drift and fails validation.

## Validation

Require the frontmatter fields (`kind`, `schema`, `run_id`, `step_id`,
`chunk_id`, `type`) and every template heading, including `Contract`.
Every `Requirements Covered` entry names only requirement IDs from its own
Contract, and every contract-assigned requirement appears in at least one
step of the chunk. Contract sections must be verbatim-identical across all
steps sharing a `chunk_id`. A behavioral unit keeps its primary-test step
immediately before its implementation step within the chunk.
