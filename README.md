# Implementation Agent Workflow

A resumable, test-driven workflow for implementing a design specification or implementation
plan with isolated subagents.

## Why this exists

Large plans become easier to execute when each step has a small context, explicit acceptance
criteria, persistent status, and an independent verification pass. This bundle provides the
agents and skills for that workflow without duplicating files across tool-specific directories.

The workflow:

1. Audits the plan for blockers and unclear interfaces.
2. Splits behavior into a failing-test step and an implementation step.
3. Verifies every step before continuing.
4. Persists state so an interrupted run can resume.
5. Uses a clean implementation branch when Git is available.
6. Documents the finished implementation and verifies the documentation.

## Layout

- `agents/`: canonical custom agent definitions.
- `skills/`: canonical reusable workflow skills, hidden from automatic model discovery.
  Every SKILL.md sets `disable-model-invocation: true`, so hosts that honor the flag omit them
  from the model's discovered-skill list; each loads only when an agent instruction or another skill
  calls it by name and stays reachable through `skill://<name>`. All set
  `user-invocable: false` except 7 user-facing entry points:
  - `implementation-orchestrator`
  - `model-configuration`
  - `plan-audit`
  - `plan-decomposition`
  - `systematic-debugging`
  - `test-driven-development`
  - `verification-before-completion`
   Each gates its workflow-specific outputs so a direct invocation produces no persisted artifacts,
   while delegated role agents persist them as before.
- `package.json`: Pi/oh-my-pi package manifest. It exposes the same agent Markdown as prompt
resources and the same skills as Agent Skills.
- `plugin.json`: Copilot plugin manifest. It exposes the same `agents/` and `skills/`
directories without copying them into a project.
- `.agent-work/`: created by the orchestrator at runtime; keep it untracked.

There is deliberately no separate copy for Copilot CLI or Pi/oh-my-pi. Copilot CLI installs the
repository as a plugin, while Pi and oh-my-pi install it as a Pi package. Both manifests point
to the same `agents/` and `skills/` directories.

## Install for Pi or oh-my-pi

Install the repository directly as a Pi package; the package manifest handles discovery:

```bash
pi install git:github.com/OWNER/implementation-agent-workflow
```

For oh-my-pi, use its package installer with the same repository source:

```bash
omp install git:github.com/OWNER/implementation-agent-workflow
```

Use the project-local form when the workflow should apply to one repository only:

```bash
pi install -l git:github.com/OWNER/implementation-agent-workflow
```

The installed package contributes the workflow skills and exposes the eight role files as
prompt resources. The role files are not copied into a second Pi-specific directory.
Because the bundled skills set `disable-model-invocation`, hosts that honor the flag omit
them from automatic model skill discovery; they load only when a role file or another
skill invokes them by name.

## Install as a Copilot plugin

Copilot CLI installs plugins from a GitHub repository, Git URL, marketplace, or local
directory. The root `plugin.json` points Copilot at the canonical `agents/` and `skills/`
directories, so no project files need to be copied or linked.

From a GitHub repository:

```bash
copilot plugin install OWNER/implementation-agent-workflow
```

From a local checkout while developing:

```bash
copilot plugin install .
```

Verify and manage the installation:

```bash
copilot plugin list
copilot plugin update implementation-agent-workflow
copilot plugin uninstall implementation-agent-workflow
```

For a marketplace installation:

```bash
copilot plugin install implementation-agent-workflow@MARKETPLACE-NAME
```

After changing a local plugin, reinstall it because Copilot CLI caches installed plugin
components. Use `/agent` and `/skills list` inside a Copilot session to verify discovery.

## Running the workflow

Start the workflow with the plan path and optional audit/retry settings. The canonical
orchestrator instructions live in
[`skills/implementation-orchestrator`](skills/implementation-orchestrator/SKILL.md).
In VS Code or Copilot CLI, select `Implementation Orchestrator`; its agent file is a
thin wrapper that explicitly invokes that skill. In Pi/oh-my-pi, invoke the installed
prompt corresponding to `implementation-orchestrator.agent.md`.

Or invoke the user-invocable `implementation-orchestrator` skill directly.
The invocation input should contain:

```text
Plan: path/to/plan.md
Run directory: .agent-work/run-001
Maximum retries per verification loop: 2
Skip plan audit: false
```

The orchestrator writes all handoff files, reports, and checkpoints under `.agent-work/`. It
never commits those files. Add `.agent-work/` to `.git/info/exclude` if desired.

## Model configuration and routing

Portable model selection is configured separately from workflow roles. The repository
catalog and policy normally live at:

```text
.implementation-agent/model-catalog.yaml
.implementation-agent/model-policy.yaml
```

Use the separately invocable [`model-configuration`](skills/model-configuration/SKILL.md)
skill to create or edit them. It asks for structured capabilities, tier, cost,
`context_window`, tools, host mappings, role requirements, fallback chains, retry
behavior, and `require_application`. It validates the complete YAML result, preserves
unrelated fields during field-level merges, and requires confirmation before writing.
Model IDs and host mappings are data, never executable commands. The catalog and policy
schemas are defined by [`model-catalog-format`](skills/model-catalog-format/SKILL.md).

A minimal catalog entry and role policy look like this:

```yaml
# .implementation-agent/model-catalog.yaml
models:
  - id: coding-standard
    capabilities: [coding, testing]
    tier: 1
    cost: medium
    context_window: 128000
    tools: [read, search, edit, execute]
    hosts:
      copilot: Code Model (copilot)
      omp: anthropic/claude-sonnet-4-5
```

```yaml
# .implementation-agent/model-policy.yaml
model_policy:
  roles:
    implementer:
      required_capabilities: [coding, testing]
      minimum_tier: 1
      default: coding-standard
  fallback: cheap-general
  retry:
    preserve_assignment: true
    allow_escalation: false
  host:
    require_application: false
```

These repository files are configuration inputs, not run state. After confirmed
invocation overrides are merged and validated, the orchestrator freezes effective copies
under `.agent-work/<run-id>/model-catalog.yaml` and
`.agent-work/<run-id>/model-policy.yaml`. Resumed runs use those copies rather than
silently rereading changed repository files. An invocation override requires a complete
effective-configuration display and explicit confirmation; declining it cancels the write and
leaves the repository files unchanged.

### Runtime evidence

The portable `requested` ID, adapter `resolved` model, `fallback`, `applied` result,
`runtime_model`, `warning`, and `evidence` are separate facts in the run records. A
resolved model is not necessarily an applied model. The delegation guide in
[`model-routing-adapter`](skills/model-routing-adapter/SKILL.md) defines these evidence
levels:

- `adapter-confirmed`: deterministic host or tool confirmation of the resolved model;
- `host-reported`: the host exposed a runtime model without confirming the override;
- `self-reported`: the delegated agent reported what it observed;
- `unknown`: no runtime model evidence was available.

Only `adapter-confirmed` supports the strongest claim that a requested model was
applied; runs without such deterministic confirmation can record at most `host-reported`
or `self-reported` evidence for their applied results. A fallback, default model, host
mismatch, or unavailable application mechanism must include a warning with the exact
reason. With `require_application: true`, an unconfirmed application blocks rather than
silently continuing. Retries preserve the assignment by default; escalation requires
explicit policy approval and a new attempt record.

### Host support and scope

Model delegation uses whatever per-delegation `model` mechanism the active host
exposes. A one-time capability probe at run start confirms whether that mechanism
works for the session and pins how evidence is obtained (delegation response payload
or subagent self-report). Runs without a confirmed mechanism delegate without a model
field and record routing-unavailable warnings; on Pi the static check finds no exposed
per-delegation `model` parameter, so such runs take the routing-unavailable path.

The simplified approach uses zero compiled adapters. Model resolution happens entirely
through YAML catalog lookup, a one-time capability probe, and per-delegation `model`
field delegation:

1. The orchestrator reads the effective run copy `.agent-work/<run-id>/`
`model-catalog.yaml` to map the selected portable ID to a host-specific
model name via `hosts.<host>`.
2. A one-time capability probe (a cheap self-identification delegation)
confirms whether the active host honors per-delegation model selection and pins
the evidence channel for the run.
3. When confirmed, the `model` field is set on each delegation; otherwise
no model field is set and warnings are recorded.

No TypeScript, no host bridges, no package extensions. The catalog and policy are pure
YAML configuration files that can be edited independently of the workflow code.

**Migration from compiled adapters:** If you previously read the OMP adapter plan or
Copilot adapter plan, those approaches are replaced. The portable ID vocabulary,
evidence levels, and assignment field contracts remain unchanged - only the mechanism
changed from TypeScript bridges to catalog YAML lookup + `model` field delegation gated
by a one-time capability probe.

## Inter-agent communication

Every delegated agent returns exactly one `agent-handoff/v1` report, as defined by the
[`agent-handoff`](skills/agent-handoff/SKILL.md) format skill. The report is the sole
communication contract between agents; role-specific results are carried in its requirement,
validation, artifact, and blocker fields.

Required top-level fields are `schema`, `agent`, `task`, `status`, `summary`, `inputs`,
`details`, `requirements`, `validation`, `artifacts`, `repository`, `blockers`, and
`resume_from`. Role-specific payloads go under `details`. File-modifying agents list all
changed files and commits. Read-only agents use empty change and commit lists. Every
requirement and validation result includes evidence.

The orchestrator validates the schema, role-allowed status, status-specific fields, and
evidence before consuming a result. A missing or malformed handoff is persisted as `BLOCKED`;
success is never inferred from an agent narrative, changed files, or an absent validation
result. `VERIFIED` is reserved for verifier roles with executable evidence for every material
requirement.

The retry limit counts repair attempts after the initial attempt. For example, a limit of `2`
permits at most three implementer attempts for one verification loop. `INCOMPLETE` consumes one
repair attempt; `BLOCKED`, malformed handoffs, and `NEEDS_CLARIFICATION` stop the workflow
without consuming a repair attempt. A step is `completed` only after its verifier returns
`VERIFIED`.

## Details: full workflow

The workflow is coordinated by `Implementation Orchestrator`. The orchestrator owns sequencing,
persistent status, retry limits, and user-facing reports. Specialist agents do the plan reading
and repository work in isolated contexts. The orchestrator should read summaries and reports
rather than loading the entire plan into its own context.

### 1. Start the run

The orchestrator receives the plan path, run directory, retry limit, and optional
`Skip plan audit` setting. It creates an untracked run directory such as `.agent-work/run-001/`
and writes the initial `run.yaml` using
[`run-ledger-format`](skills/run-ledger-format/SKILL.md) before starting another agent.

The run directory contains the durable coordination state:

```text
.agent-work/run-001/
	run.yaml
	plan-audit.yaml
	documentation/
		source-documentation-context.md
		user-documentation-context.md
	step-index.yaml
	steps/
		<step-id>.md
		<step-id>-status.yaml
	reports/
		<phase>-<subject>-<attempt>.yaml
	checkpoints/
		<step-id>.yaml
	documentation/
		<assignment-id>.md
	final-report.yaml
```

Every status update records the phase, step, attempt, assigned agent, status, branch, last
known commit, changed files, validation evidence, timestamps, blockers, and resume
instructions. YAML is used for machine-validated state and reports. Step and documentation
context use Markdown with required YAML frontmatter and stable headings. No extensionless,
JSON, or ad hoc text artifacts are permitted. YAML state and reports are written atomically.
The run directory is never committed.

### 2. Prepare Git isolation

When the target workspace is a Git repository, `Implementation Orchestrator` uses
`git-isolated-implementation` before any file-modifying subagent starts:

1. Require no tracked staged or unstaged changes.
2. Preserve all existing untracked files.
3. Record the starting branch and commit.
4. Create and record a new implementation branch.
5. Keep all implementation commits on that branch.

If a subagent needs multiple experimental commits, it creates a temporary child branch and
merges the verified result back into the implementation branch. The orchestrator never resets
or discards unrelated work.

### 3. Audit the plan: `Plan Auditor` (Subagent A)

Unless the user explicitly skips the audit, the orchestrator starts `Plan Auditor` with the
plan. The agent uses `plan-audit` and `requirements-traceability` to check:

- Contradictions and missing requirements.
- Blocking ambiguity and undefined external interfaces.
- Impossible or unsupported requirements.
- Hidden dependencies and unnecessary complexity.
- Missing acceptance criteria or validation commands.

The auditor writes `plan-audit.yaml` using
[`plan-audit-format`](skills/plan-audit-format/SKILL.md), with `PASS`, `NEEDS_CLARIFICATION`,
or `BLOCKED`, plus findings, required questions, external interfaces, and validation gaps.

If the result is `NEEDS_CLARIFICATION` or `BLOCKED`, the orchestrator reports the findings to
the user and stops. No implementation work begins. A `PASS` permits decomposition.

The audit also creates separate Markdown briefs for source and user documentation under
`documentation/`, using
[`documentation-context-format`](skills/documentation-context-format/SKILL.md).
`plan-audit.yaml` records their paths and status. The orchestrator carries the relevant brief
into later documentation assignments, where it is reconciled with the verified implementation
and changed files. This prevents documentation agents from rereading the complete plan while
keeping the implementation authoritative.

### 4. Decompose the plan: `Step Decomposer` (Subagent B)

The orchestrator starts `Step Decomposer` with the approved plan and audit result. The agent
uses `plan-decomposition`, `test-first-plan-steps`, `requirements-traceability`, and
`persistent-workflow-state`.

For every behavioral unit, the decomposer creates two ordered context files:

1. **Primary-test step:** defines the external behavior, writes focused tests, and proves they
fail for the intended reason.
2. **Implementation step:** implements the behavior required by those primary tests and may add
justified supplementary tests.

Purely mechanical or infrastructure work may be marked `non-behavioral`, but the context file
must explain why a failing test is not meaningful.

Each `steps/<step-id>.md` file follows
[`step-context-format`](skills/step-context-format/SKILL.md), including explanatory guidance
and examples for its objective, requirement IDs, dependencies, interfaces, likely files,
implementation scope, acceptance criteria, validation commands, expected failure or success,
exclusions, and commit expectations. The decomposer writes `step-index.yaml` using
[`step-index-format`](skills/step-index-format/SKILL.md) with dependency order, and reports a
concise step list to the orchestrator.

### 5. Execute and verify each step

The orchestrator processes the dependency-ordered steps one at a time. A dependent step does
not start until its predecessor is verified.

#### 5a. Implement the step: `Step Implementer` (Subagent C)

Before launching the agent, the orchestrator persists the step as `running` using
[`step-status-format`](skills/step-status-format/SKILL.md). `Step Implementer` reads the step
context, its checkpoint, and any prior verifier report using
[`step-context-format`](skills/step-context-format/SKILL.md) and
[`checkpoint-format`](skills/checkpoint-format/SKILL.md). It uses:

- `implementation-execution` for bounded repository changes.
- `test-driven-development` for behavioral work.
- `test-first-plan-steps` to preserve the primary-test/implementation boundary.
- `git-isolated-implementation` for branch and commit rules.
- `persistent-workflow-state` and `subagent-recovery` for checkpoints and interruption
handling.
- `requirements-traceability` for requirement and validation reporting.
- `atomic-step-commit` for the final validate/commit/status sequence.
- `systematic-debugging` when a focused check fails unexpectedly.

For a primary-test step, the agent writes only the planned tests, runs them, and records the
intentional failure. For an implementation step, it makes the smallest production change that
passes the primary tests, adding supplementary tests only when needed for discovered edge cases
or regressions.

When files were modified, the agent's final sequence is:

```text
run focused validation -> create step commit -> persist commit hash -> report
```

If the agent is interrupted or blocked by connection loss, cancellation, unavailable resources,
or permissions, it persists a recoverable status and leaves the workspace intact.

#### 5b. Verify the step: `Step Verifier` (Subagent D)

After the implementation agent returns, the orchestrator starts `Step Verifier` with the step
context, implementation report, and repository state. The verifier is read-only and uses
`verification-before-completion`, `requirements-traceability`, and `test-first-plan-steps`.

For a primary-test step, it confirms that the tests express the required behavior and fail for
the intended reason. For an implementation step, it confirms that:

- Acceptance criteria are satisfied.
- Required tests pass.
- The recorded commit contains the expected changes.
- Scope has not expanded unexpectedly.
- External interfaces remain compatible.

The verifier writes `VERIFIED`, `INCOMPLETE`, or `BLOCKED`, with requirement results,
validation evidence, missing work, blockers, and a resume point.

#### 5c. Repair an incomplete step

If verification returns `INCOMPLETE`, the orchestrator starts `Step Implementer` again with the
verifier report. The implementation agent repairs only that step, then commits the correction.
The orchestrator reruns `Step Verifier`.

This loop continues only up to the configured retry limit. A `BLOCKED` result or exhausted
retry limit is reported to the user with the current branch, commit, changed files, and resume
instructions. Completed and verified steps are not restarted.

### 6. Verify the complete implementation: `Final Verifier` (Subagent E)

After every step is verified, the orchestrator starts `Final Verifier` with the plan, step
index, all reports, commit history, and repository state. It uses
`verification-before-completion`, `requirements-traceability`, `git-isolated-implementation`,
and `persistent-workflow-state`.

The final verifier checks:

- Every plan requirement is satisfied.
- Test and implementation steps form the intended TDD sequence.
- Cross-step behavior is coherent.
- External interfaces match the plan.
- Important edge cases have validation coverage.
- Every implementation change is traceable to a commit.
- `.agent-work/` and unrelated artifacts are absent from implementation commits.
- The final branch and worktree obey the Git policy.

It writes a requirement-to-test-step-to-implementation-step-to-commit-to-validation matrix and
returns `VERIFIED`, `INCOMPLETE`, or `BLOCKED`.

If final verification fails, the orchestrator starts `Step Implementer` with the final report
and affected step contexts, then reruns `Final Verifier` within the retry limit.

### 7. Document affected source files: `Documentation Agent` (Subagent F)

Once the implementation is verified, the orchestrator builds a documentation assignment for
each affected source file that needs maintainer-facing documentation. Independent assignments
may run in parallel when they do not share ownership or create conflicting edits.

For each assignment, `Documentation Agent` reads the relevant Markdown documentation context,
implementation context, and interfaces. It uses `source-documentation`,
`documentation-verification`, `requirements-traceability`, `git-isolated-implementation`,
`persistent-workflow-state`, and `atomic-step-commit`. The assignment should contain the
relevant requirements and context; the verified implementation is authoritative.

It documents public interfaces, invariants, side effects, error contracts, lifecycle
constraints, and non-obvious behavior. It does not narrate obvious code or change
implementation behavior. Documentation changes are validated and committed separately.

### 8. Verify source documentation: `Documentation Verifier` (Subagent G)

The orchestrator starts `Documentation Verifier` for each source-documentation assignment. It
uses `documentation-verification`, `source-documentation`, `requirements-traceability`, and
`verification-before-completion`.

The verifier checks only material issues:

- Missing public behavior or constraints.
- Incorrect documentation.
- Contradictions with the implementation.
- Missing important interfaces, prerequisites, or limitations.

It does not request stylistic rewrites. Failed documentation verification returns to
`Documentation Agent` with the report and repeats within the retry limit.

### 9. Create and verify user documentation

After source documentation is stable, the orchestrator starts `Documentation Agent` for the
user-facing documentation set using `documentation/user-documentation-context.md` plus verified
implementation evidence. The agent uses `user-documentation`, `documentation-verification`, and
`requirements-traceability` to document supported workflows, prerequisites, configuration,
commands, expected results, examples, limitations, and recovery guidance without rereading the
complete plan.

The orchestrator then starts `Documentation Verifier` with the plan, implementation reports,
public interfaces, and user documentation. It checks correctness and material completeness, not
wording preferences. Failed verification returns to `Documentation Agent` and repeats within
the retry limit.

### 10. Finish and report

The orchestrator performs a final repository check and writes `final-report.yaml` using
[`final-report-format`](skills/final-report-format/SKILL.md). It records:

- Plan audit result.
- Completed and verified steps.
- Test and validation commands with results.
- Implementation and documentation commit hashes.
- Requirement traceability status.
- Current branch and worktree status.
- Documentation updated.
- Blockers, warnings, or intentionally skipped work.
- Resume instructions if the run did not complete.

Only after this final status is persisted may the orchestrator report the workflow as complete.

## Recovery and Git rules

If a subagent is interrupted or blocked, the orchestrator records the state and reports the
blocker. Resume the existing run; do not restart completed steps. Tracked repositories must
start clean and use a new implementation branch. Untracked user files are preserved.
File-modifying subagents commit completed work before returning; temporary child branches are
used when multiple commits are needed.

This bundle is a workflow template, not a replacement for repository-specific tests,
permissions, or host documentation.

## Host capability note

The shared files describe the roles and procedures. Copilot CLI loads them through
`plugin.json`; Pi/oh-my-pi loads them through `package.json`. Both manifests point to the same
`agents/` and `skills/` directories. Full automatic step orchestration in Pi/oh-my-pi would
require a TypeScript extension, which is intentionally not duplicated into this content-only
bundle yet.
