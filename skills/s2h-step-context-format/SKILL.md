---
name: s2h-step-context-format
description: Only use when explicitly invoked
# description: "Defines the Markdown template and writing guidance for
# implementation step context files."
user-invocable: false
disable-model-invocation: true
---
# Step Context Format

Use this skill when the decomposer defines a chunk contract, and when
chunk writers create or verifiers validate `steps/<step-id>.md`. The
`Contract` section's requirement excerpts come verbatim from the run's
`requirements.json`.

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

The frontmatter MUST be flat scalar key-value lines; quoted values are
supported, and folded or multi-line values, list items, flow collections,
and comments produce a named FAIL naming the offending key. Require non-empty
`kind`, `schema`, `run_id`, `step_id`, `chunk_id`, `type`; `kind` is
"step-context" and `schema` is "step-context/v1".

Every template heading MUST be present, including `Contract`. Every bullet in
`Contract` and `Requirements Covered` MUST take the form `<id>: <excerpt>`
with a non-empty id. Each `Requirements Covered` bullet's id MUST be a member
of that file's own Contract bullet ids; an empty `Requirements Covered`
bullet list is a FAIL. Ids are arbitrary non-empty strings - no shape rule.

Contract sections MUST be verbatim-identical across all steps sharing one
`chunk_id`.

The rules above are enforced by `scripts/validate.py <file> [files...]`, which
exits 0 only on pass; the script enforces these rules but never defines them.
Before persisting a step context file: MUST run the validator on it together
with every other step file of its chunk in one invocation so the cross-file
Contract check applies, and the files MUST pass validation before persistence.
The script is located relative to this skill's directory.

Verbatim identity compares tokens, not newline or indentation placement. A
Contract bullet's plan excerpt may render a multi-line `requirements.json` entry
on one line, or keep it across lines; newlines and leading whitespace inside an
excerpt are non-structural and MUST NOT be treated as a verbatim failure. A
verifier MUST judge each step file against the token content of its own Contract
excerpts; it MUST NOT cross-check sibling chunks' formatting to decide consistency.
