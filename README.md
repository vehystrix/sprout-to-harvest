# Sprout To Harvest

**sprout-to-harvest**: plant a design specification, grow it through small independently verified
steps, and harvest the finished, verified result.

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

## Terms

- **Chunk**: one behavioral or non-behavioral unit of work owned by exactly one writer,
  described in `chunk-index.json`.
- **Step**: one executable step inside a chunk; test-first steps come before their
  implementation steps. Each is written as `steps/<step-id>.md` per `s2h-step-context-format`.

## Layout

- `agents/`: canonical custom agent definitions.
- `skills/`: canonical reusable workflow skills, hidden from automatic model discovery.
  Every SKILL.md sets `disable-model-invocation`; all set `true` - hidden from
  automatic model discovery - except `s2h-verification-before-completion`,
  which sets `false` so a model may apply its guidance mid-task. Each loads when an agent
  instruction calls it by name and stays reachable through `skill://<name>`.
  All set `user-invocable: false` except 8 user-facing entry points:
  - `s2h-design`
  - `s2h-orchestrator`
  - `s2h-model-config`
  - `s2h-plan-audit`
  - `s2h-plan-decomposition`
  - `s2h-systematic-debugging`
  - `s2h-tdd`
  - `s2h-verification-before-completion`

   The others gate their workflow-specific outputs so a direct invocation produces no
   persisted artifacts; two deliverable writers are exceptions: `s2h-design` writes only
   the design document(s), and `s2h-plan-decomposition` writes the implementation step files
   plus a deletable `.work/` communication directory at the user-specified location, both with
   no workflow state. Delegated role agents persist their outputs as before.
- `templates/`: model catalog and policy JSON templates; target repositories
  copy them to `.sprout-to-harvest/model-catalog.json` and
  `.sprout-to-harvest/model-policy.json`.
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
pi install git:github.com/vehystrix/sprout-to-harvest
```

For oh-my-pi, use its package installer with the same repository source:

```bash
omp install git:github.com/vehystrix/sprout-to-harvest
```

Use the project-local form when the workflow should apply to one repository only:

```bash
pi install -l git:github.com/vehystrix/sprout-to-harvest
```

The installed package contributes the workflow skills and exposes the eleven role files as
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
copilot plugin install vehystrix/sprout-to-harvest
```

From a local checkout while developing:

```bash
copilot plugin install .
```

Verify and manage the installation:

```bash
copilot plugin list
copilot plugin update sprout-to-harvest
copilot plugin uninstall sprout-to-harvest
```

After changing a local plugin, reinstall it because Copilot CLI caches installed plugin
components. Use `/agent` and `/skills list` inside a Copilot session to verify discovery.

## Running the workflow

If you do not yet have an approved plan, build it interactively with the
user-invocable [`s2h-design`](skills/s2h-design/SKILL.md) skill; for small scopes its
single document is the immutable `Plan:` input for the orchestrator invocation below.
For large systems it produces a tiered tree of documents whose leaves serve that role.

Start the workflow with the plan path and optional audit/retry settings. The canonical
orchestrator instructions live in
[`skills/s2h-orchestrator`](skills/s2h-orchestrator/SKILL.md).
In VS Code or Copilot CLI, select `s2h-OrchestratorAgent`; its agent file is a
thin wrapper that explicitly invokes that skill. In Pi/oh-my-pi, invoke the installed
prompt corresponding to `s2h-orchestrator-agent.agent.md`.

Or invoke the user-invocable `s2h-orchestrator` skill directly.
The invocation input should contain:

```text
Plan: path/to/plan.md
Run directory: .agent-work/run-001
Maximum retries per verification loop: 2
Skip plan audit: false
```

The orchestrator writes all handoff files, reports, and checkpoints under `.agent-work/`. It
never commits those files. Add `.agent-work/` to `.gitignore` if desired.

## Model configuration and routing

Portable model selection is configured separately from workflow roles. The repository
catalog and policy normally live at:

```text
.sprout-to-harvest/model-catalog.json
.sprout-to-harvest/model-policy.json
```

Use the separately invocable [`s2h-model-config`](skills/s2h-model-config/SKILL.md)
skill to create or edit them. It asks for structured capabilities, tier, cost, optional
`reasoning_effort` settings, `context_window`, host mappings, role requirements,
fallback chains, retry behavior, and `require_application`. It validates the complete JSON
result, preserves unrelated fields during field-level merges, and requires confirmation
before writing.
Model IDs and host mappings are data, never executable commands. The catalog and policy
schemas are defined by `s2h-model-catalog-format`.

A minimal catalog entry and role policy look like this:

```json
{
  "models": [
    {
      "id": "coding-standard",
      "capabilities": ["coding", "testing"],
      "tier": 1,
      "cost": "medium",
      "context_window": 128000,
      "hosts": {
        "copilot": "Code Model (copilot)",
        "omp": "anthropic/claude-sonnet-4-5"
      }
    }
  ]
}
```

```json
{
  "model_policy": {
    "roles": {
      "implementer": {
        "required_capabilities": ["coding", "testing"],
        "minimum_tier": 1,
        "default": "coding-standard"
      }
    },
    "fallback": "cheap-general",
    "retry": {
      "preserve_assignment": true,
      "allow_escalation": false
    },
    "host": {
      "require_application": false
    }
  }
}
```

These repository files are configuration inputs, not run state. After confirmed
invocation overrides are merged and validated, the orchestrator freezes effective copies
under `.agent-work/<run-id>/model-catalog.json` and
`.agent-work/<run-id>/model-policy.json`. Resumed runs use those copies rather than
silently rereading changed repository files. An invocation override requires a complete
effective-configuration display and explicit confirmation; declining it cancels the write and
leaves the repository files unchanged.

### Runtime evidence

The portable `requested` ID, adapter `resolved` model, `fallback`, `applied` result,
`runtime_model`, `warning`, and `evidence` are separate facts in the run records. A
resolved model is not necessarily an applied model. The delegation guide in
`s2h-model-routing-adapter` defines these evidence levels:

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

Model resolution happens entirely through JSON catalog lookup, a one-time capability probe,
and per-delegation `model` field delegation:

1. The orchestrator reads the effective run copy `.agent-work/<run-id>/`
`model-catalog.json` to map the selected portable ID to a host-specific
model name via `hosts.<host>`.
2. A one-time capability probe (a cheap self-identification delegation)
confirms whether the active host honors per-delegation model selection and pins
the evidence channel for the run.
3. When confirmed, the `model` field is set on each delegation; otherwise
no model field is set and warnings are recorded.

## Inter-agent communication

Every delegated agent returns exactly one `s2h-handoff/v1` report, as defined by the
`s2h-handoff` format skill. The report is the sole communication contract between agents;
role-specific results are carried in its requirement, validation, artifact, and blocker fields.

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

The workflow is coordinated by `s2h-OrchestratorAgent`. The orchestrator owns sequencing,
persistent status, retry limits, and user-facing reports. Specialist agents do the plan reading
and repository work in isolated contexts. The orchestrator should read summaries and reports
rather than loading the entire plan into its own context.

### 1. Start the run

The orchestrator receives the plan path, run directory, retry limit, and optional
`Skip plan audit` setting. It creates an untracked run directory such as `.agent-work/run-001/`
and writes the initial `run.json` using `s2h-run-ledger-format` before starting another agent.

The run directory contains the durable coordination state:

```text
.agent-work/run-001/
	run.json
	s2h-plan-audit.json
	documentation/
		source-doc-context.md
		user-doc-context.md
	requirements.json
	chunk-index.json
	steps/
		<step-id>.md
		<step-id>-status.json
	reports/
		<phase>-<subject>-<attempt>.json
	checkpoints/
		<step-id>.json
	documentation/
		<assignment-id>.md
	final-report.json
```

Every status update records the phase, step, attempt, assigned agent, status, branch, last
known commit, changed files, validation evidence, timestamps, blockers, and resume
instructions. JSON is used for machine-validated state and reports. Step and documentation
context use Markdown with required YAML frontmatter and stable headings. No extensionless,
YAML, or ad hoc text artifacts are permitted. JSON state and reports are written atomically.
The run directory is never committed.

### 2. Prepare Git isolation

When the target workspace is a Git repository, `s2h-OrchestratorAgent` uses
`s2h-git-isolation` before any file-modifying subagent starts:

1. Require no tracked staged or unstaged changes.
2. Preserve all existing untracked files.
3. Record the starting branch and commit.
4. Create and record a new implementation branch.
5. Keep all implementation commits on that branch.

If a subagent needs multiple experimental commits, it creates a temporary child branch and
merges the verified result back into the implementation branch. The orchestrator never resets
or discards unrelated work.

### 3. Audit the plan: `s2h-PlanAuditor`

Unless the user explicitly skips the audit, the orchestrator starts `s2h-PlanAuditor` with the
plan. The agent uses `s2h-plan-audit` and `s2h-requirements-traceability` to check:

- Contradictions and missing requirements.
- Blocking ambiguity and undefined external interfaces.
- Impossible or unsupported requirements.
- Hidden dependencies and unnecessary complexity.
- Missing acceptance criteria or validation commands.

The auditor writes `s2h-plan-audit.json` using `s2h-plan-audit-format`, with `PASS`,
`NEEDS_CLARIFICATION`, or `BLOCKED`, plus findings, required questions, external interfaces,
and validation gaps.

It also extracts the complete requirements list, including implied-only
requirements; on a PASS it writes `requirements.json` and records
the path in its handoff. The orchestrator records that path for decomposition.
If the result is `NEEDS_CLARIFICATION` or `BLOCKED`, the orchestrator reports the findings to
the user and stops. No implementation work begins. A `PASS` permits decomposition.

The audit also creates separate Markdown briefs for source and user documentation under
`documentation/`, using `s2h-doc-context-format`. `s2h-plan-audit.json` records their paths and
status. The orchestrator carries the relevant brief into later documentation assignments, where
it is reconciled with the verified implementation and changed files. This prevents documentation
agents from rereading the complete plan while keeping the implementation authoritative.

### 4. Decompose the plan: `s2h-PlanDecomposer`, `s2h-ChunkWriter`, `s2h-ChunkVerifier`,
`s2h-WholePlanVerifier`

The orchestrator delegates decomposition exactly once to `s2h-PlanDecomposer`. The decomposer owns
the whole phase, using [`s2h-plan-decomposition`](skills/s2h-plan-decomposition/SKILL.md) and
the plan's requirements list: it chunks the plan by behavioral units - each chunk owns a contract
of assigned requirement IDs with verbatim plan excerpts, interfaces in/out, an end-state, and
exclusions, and every inventory requirement is owned by exactly one chunk - writes
`chunk-index.json` using `s2h-chunk-index-format` with the dependency order and model
recommendations, then runs each chunk's writer and verifier loop.

For each chunk, `s2h-ChunkWriter` creates that chunk's `steps/<step-id>.md` files per
`s2h-step-context-format`, embedding the contract verbatim in every file; `s2h-ChunkVerifier`
is read-only and confirms traceability for every requirement the chunk owns. Each writer and
verifier loop gets its own repair cap: the same `L` passed to implementation and documentation
loops. An exhausted allowance blocks the run with that chunk's evidence.

After all chunks verify, `s2h-WholePlanVerifier` performs only global checks no single
chunk can see - unassigned content, duplicate ownership, and boundary consistency
against the full plan. A `decomposition-gap` finding - one requiring a change to
chunk assignments or boundaries - is repaired by the decomposer itself, which reruns
the affected writer and verifier loops; a `boundary-mismatch` reruns the affected
writer loops only. Each repair runs as a fresh loop instance under the same cap.
Whole-plan verifications total at most `L + 1`.

You can also run this pipeline directly as a user: invoke
[`s2h-plan-decomposition`](skills/s2h-plan-decomposition/SKILL.md) with the plan and an
Output directory. It writes the deliverable `chunk-index.json`, step context
and status files,
derived `requirements.json` under `<output-dir>/.work/` (step files
under `.work/steps/`); re-invoking the same inputs resumes from verified chunks.

### 5. Execute and verify each step

The orchestrator processes the dependency-ordered steps one at a time. A dependent step does
not start until its predecessor is verified.

#### 5a. Implement the step: `s2h-StepImplementer`

Before launching the agent, the orchestrator persists the step as `running` using
`s2h-step-status-format`. `s2h-StepImplementer` reads the step context, its checkpoint, and
any prior verifier report using `s2h-step-context-format` and `s2h-checkpoint-format`. It uses:

- `s2h-implementation` for bounded repository changes.
- `s2h-tdd` for behavioral work.
- `s2h-test-first-plan-steps` to preserve the primary-test/implementation boundary.
- `s2h-git-isolation` for branch and commit rules.
- `s2h-persistent-state` and `s2h-subagent-recovery` for checkpoints and interruption
handling.
- `s2h-requirements-traceability` for requirement and validation reporting.
- `s2h-atomic-step-commit` for the final validate/commit/status sequence.
- `s2h-systematic-debugging` when a focused check fails unexpectedly.

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

#### 5b. Verify the step: `s2h-StepVerifier`

After the implementation agent returns, the orchestrator starts `s2h-StepVerifier` with the step
context, implementation report, and repository state. The verifier is read-only and uses
`s2h-verification-before-completion`, `s2h-requirements-traceability`, and `s2h-test-first-plan-steps`.

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

If verification returns `INCOMPLETE`, the orchestrator starts `s2h-StepImplementer` again with the
verifier report. The implementation agent repairs only that step, then commits the correction.
The orchestrator reruns `s2h-StepVerifier`.

This loop continues only up to the configured retry limit. A `BLOCKED` result or exhausted
retry limit is reported to the user with the current branch, commit, changed files, and resume
instructions. Completed and verified steps are not restarted.

### 6. Verify the complete implementation: `s2h-FinalVerifier`

After every step is verified, the orchestrator starts `s2h-FinalVerifier` with the plan, step
index, all reports, commit history, and repository state. It uses
`s2h-verification-before-completion`, `s2h-requirements-traceability`, `s2h-git-isolation`,
and `s2h-persistent-state`.

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

If final verification fails, the orchestrator starts `s2h-StepImplementer` with the final report
and affected step contexts, then reruns `s2h-FinalVerifier` within the retry limit.

### 7. Document affected source files: `s2h-DocumentationWriter`

Once the implementation is verified, the orchestrator builds a documentation assignment for
each affected source file that needs maintainer-facing documentation. Independent assignments
may run in parallel when they do not share ownership or create conflicting edits.

For each assignment, `s2h-DocumentationWriter` reads the relevant Markdown documentation context,
implementation context, and interfaces. It uses `s2h-source-doc`,
`s2h-doc-verification`, `s2h-requirements-traceability`, `s2h-git-isolation`,
`s2h-persistent-state`, and `s2h-atomic-step-commit`. The assignment should contain the
relevant requirements and context; the verified implementation is authoritative.

It documents public interfaces, invariants, side effects, error contracts, lifecycle
constraints, and non-obvious behavior. It does not narrate obvious code or change
implementation behavior. Documentation changes are validated and committed separately.

### 8. Verify source documentation: `s2h-DocumentationVerifier`

The orchestrator starts `s2h-DocumentationVerifier` for each `s2h-source-doc` assignment. It
uses `s2h-doc-verification`, `s2h-source-doc`, `s2h-requirements-traceability`, and
`s2h-verification-before-completion`.

The verifier checks only material issues:

- Missing public behavior or constraints.
- Incorrect documentation.
- Contradictions with the implementation.
- Missing important interfaces, prerequisites, or limitations.

It does not request stylistic rewrites. Failed documentation verification returns to
`s2h-DocumentationWriter` with the report and repeats within the retry limit.

### 9. Create and verify user documentation

After source documentation is stable, the orchestrator starts `s2h-DocumentationWriter` for the
user-facing documentation set using `documentation/user-doc-context.md` plus verified
implementation evidence. The agent uses `s2h-user-doc`, `s2h-doc-verification`, and
`s2h-requirements-traceability` to document supported workflows, prerequisites, configuration,
commands, expected results, examples, limitations, and recovery guidance without rereading the
complete plan.

The orchestrator then starts `s2h-DocumentationVerifier` with the plan, implementation reports,
public interfaces, and user documentation. It checks correctness and material completeness, not
wording preferences. Failed verification returns to `s2h-DocumentationWriter` and repeats within
the retry limit.

### 10. Finish and report

The orchestrator performs a final repository check and writes `final-report.json` using
`s2h-final-report-format`. It records:

- Plan audit result.
- Completed and verified steps.
- Test and validation commands with results.
- Implementation and documentation commit hashes.
- Requirement traceability status.
- Current branch and worktree status.
- Documentation updated.
- Blockers, warnings, or intentionally skipped work.
- Resume instructions if the run did not complete.

Only after this final status is persisted will the orchestrator report the workflow as complete.

## Recovery and Git rules

If a subagent is interrupted or blocked, the orchestrator records the state and reports the
blocker. Resume the existing run; do not restart completed steps. Tracked repositories must
start clean and use a new implementation branch. Untracked user files are preserved.
File-modifying subagents commit completed work before returning; temporary child branches are
used when multiple commits are needed.

This bundle is a workflow template, not a replacement for repository-specific tests,
permissions, or host documentation.
