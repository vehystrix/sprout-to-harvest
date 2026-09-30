# Dynamic Model Selection Design

**Status:** Draft for review  
**Date:** 2026-09-14  
**Scope:** Implementation Agent Workflow  

## 1. Summary

This design adds capability-aware model selection to the implementation workflow while
keeping agent roles stable. The workflow will select models through a portable routing
layer, validate assignments centrally, persist every decision, and delegate host-specific
application to adapters.

The design supports dynamic routing for Copilot and oh-my-pi. Pi model selection is
explicitly unsupported for now. When a host cannot apply a requested model, the workflow
must report that fact and continue only according to policy; it must never imply that the
requested model was used.

## 2. Goals

- Select models by structured capabilities, tier, cost, context window, and tool support.
- Keep model selection separate from agent identity and workflow responsibilities.
- Give the orchestrator final authority over all model assignments.
- Allow the plan auditor and decomposer to establish routing requirements and hints.
- Select documentation writer and verifier models at orchestration time.
- Persist requested, resolved, fallback, and application details for every delegation.
- Make retries deterministic unless an explicit escalation policy permits a change.
- Support host-specific model application through adapters.
- Record unavailable or unapplied model requests as auditable warnings.
- Preserve resumability across interrupted runs.

## 3. Non-goals

- Replacing the host's model registry or availability system.
- Making every host support runtime model injection.
- Allowing delegated agents to select their own models.
- Automatically escalating to a more expensive model without policy approval.
- Implementing Pi model selection in this change.
- Defining provider-specific billing, quota, or authorization behavior.

## 4. Design Principles

### 4.1 Portable internal identifiers

Workflow configuration uses stable internal model IDs such as `reasoning-pro` and
`coding-standard`. Host adapters map those IDs to provider-specific names, aliases, or
roles.

### 4.2 Central enforcement

Agents may recommend models, but only the orchestrator can finalize an assignment. The
orchestrator validates IDs, capabilities, policy constraints, and host support before
launching a delegation.

### 4.3 Honest application reporting

A resolved model is not necessarily an applied model. Every adapter must report whether
the host accepted and applied the requested model. `applied: false` is a valid result and
requires a warning when execution continues with another model.

### 4.4 Immutable execution evidence

The model used for each attempt is part of the run record. Later retries must not rewrite
previous assignments. A new model assignment creates a new attempt record with its reason.

### 4.5 Independent verification

Verifier assignments are selected independently from implementer assignments. A verifier
may use a stronger reasoning model, subject to policy and availability.

## 5. Ownership and Decision Flow

### 5.1 Plan Auditor

The Plan Auditor does not make final model assignments. It records documentation and
complexity signals, including:

- Whether source documentation is required.
- Whether user documentation is required.
- Whether public APIs or configuration formats are affected.
- Whether compatibility or migration concerns are likely.
- Expected writer complexity.
- Expected verifier complexity.
- Whether independent or stronger verification is recommended.

These signals form a documentation profile in the audit result.

### 5.2 Step Decomposer

The Step Decomposer receives the model catalog and routing policy. It may recommend
implementer and verifier models for each step and records the rationale, required
capabilities, and complexity. It does not finalize or apply assignments.

The decomposer should not select documentation models because documentation assignments
are made after implementation and final verification, when changed files and actual
interfaces are known.

### 5.3 Implementation Orchestrator

The orchestrator owns final selection for:

- Plan Auditor.
- Step Decomposer.
- Step Implementer.
- Step Verifier.
- Documentation Agent.
- Documentation Verifier.

For each delegation, it:

1. Reads the applicable policy and catalog.
2. Evaluates recommendations and requirements.
3. Validates the requested model ID.
4. Resolves a host-specific model through the adapter.
5. Applies the model where the host supports it.
6. Persists the assignment before delegation.
7. Passes the assignment to the delegated agent.
8. Persists the exact result, including application status.

### 5.4 Model selection and delegation walkthrough

The complete flow for a run is:

1. **Load configuration.** The orchestrator reads the repository catalog and policy.
2. **Confirm overrides.** If invocation overrides exist, it merges them, displays the
  complete effective configuration, and waits for user confirmation.
3. **Freeze run inputs.** It validates the effective configuration and copies it under
  `.agent-work/`. These copies are used for the rest of the run.
4. **Run adapter preflight.** Before plan auditing or implementation, the selected host
  adapter verifies once that model selection works for the active session. The result is
  persisted and reused; normal delegations do not repeat this check.
5. **Determine role requirements.** The orchestrator identifies the role being delegated
  and its required capabilities, tier, context, tools, and documentation complexity.
6. **Select a portable model.** It evaluates policy defaults, user overrides, and
  decomposer recommendations, then selects and validates a catalog ID such as
  `coding-standard` or `reasoning-pro`.
7. **Resolve the host model.** The adapter maps the portable ID to a host-specific model,
  role, or generated agent profile.
8. **Persist the assignment.** The orchestrator records the requested ID, resolved model,
  rationale, fallback, adapter, and preflight reference before delegation.
9. **Apply and delegate.** The adapter applies the preflight-verified mechanism. The
  orchestrator starts the stable workflow role, such as `Step Implementer` or
  `Step Verifier`.
10. **Record evidence.** The adapter records whether selection was applied and the
   evidence level: adapter-confirmed, host-reported, self-reported, or unknown.
11. **Verify and retry if needed.** A retry reuses the same assignment by default. A
   different model is used only when an explicit escalation policy permits it, and the
   new assignment is recorded as a new attempt.

The workflow therefore separates three facts that must not be conflated: the model the
policy requested, the model the adapter resolved, and the model the host can prove was
used.

## 6. Model Catalog

The initial catalog and policy are repository configuration files. They are configuration
inputs to the workflow, not runtime state, and must not be stored under `.agent-work/`.
The recommended paths are:

```text
.implementation-agent/model-catalog.yaml
.implementation-agent/model-policy.yaml
```

The exact repository path may be configurable, but the files must remain outside
`.agent-work/` and should normally be version-controlled. The orchestrator copies the
validated, effective catalog and policy into the run directory before any delegation:

```text
.agent-work/<run-id>/model-catalog.yaml
.agent-work/<run-id>/model-policy.yaml
```

These copies are the authoritative inputs for that run. They include repository defaults
and any confirmed invocation overrides. A resumed run uses the copies rather than
silently rereading the current repository files.

### 6.1 Invocation overrides

The invocation may override individual catalog entries or policy fields. Overrides are
merged using field-level semantics defined by the configuration format; an override must
not replace unrelated defaults accidentally.

Before proceeding, the orchestrator presents the complete effective catalog and policy to
the user whenever any invocation override was supplied. The run starts only after explicit
confirmation. The confirmation must identify the changed fields and show the complete
effective configuration, not only the override fragment.

If the user declines, the run is `BLOCKED` without delegation. If no override was
supplied, the orchestrator may proceed after validating the repository files without an
additional confirmation prompt.

### 6.2 Guided configuration skill

The package includes a separately invocable skill for creating and editing the repository
catalog and policy. This skill is outside the implementation workflow and does not run as
part of orchestration. It guides the user through model capabilities, tiers, cost,
context windows, host mappings, role requirements, fallback chains, and retry policy.

The skill validates the proposed files before writing them, preserves unrelated fields,
and displays the resulting configuration for confirmation. It must not write effective
run configuration into `.agent-work/`; only the orchestrator creates those run-specific
copies.

The catalog is structured data rather than free-text descriptions. A catalog entry has
this conceptual shape:

```yaml
models:
  - id: reasoning-pro
    capabilities:
      - reasoning
      - planning
      - verification
    tier: 3
    cost: high
    context_window: 200000
    tools:
      - read
      - search
      - execute
    hosts:
      copilot: Claude Opus 4.8 (copilot)
      oh_my_pi: anthropic/claude-opus-4-8
      pi: null
```

### 6.3 Required fields

- `id`: unique portable identifier.
- `capabilities`: normalized capability names.
- `tier`: positive ranking value; higher values are stronger by default.
- `cost`: policy-comparable cost class.
- `context_window`: maximum supported context size in tokens.
- `tools`: tools required or supported by the model.
- `hosts`: optional host-specific mapping for each supported adapter.

### 6.4 Capability vocabulary

The initial vocabulary should include:

- `general`
- `orchestration`
- `reasoning`
- `planning`
- `coding`
- `testing`
- `verification`
- `documentation`
- `large-context`

Unknown capabilities are invalid unless the catalog format explicitly permits an
extension namespace.

## 7. Routing Policy

The policy defines role defaults, suitability requirements, fallback behavior, and
escalation. A conceptual configuration is:

```yaml
model_policy:
  roles:
    plan_auditor:
      required_capabilities: [reasoning, planning]
      minimum_tier: 2
    step_decomposer:
      required_capabilities: [planning, reasoning]
      minimum_tier: 2
    implementer:
      required_capabilities: [coding, testing]
      minimum_tier: 1
    verifier:
      required_capabilities: [verification, reasoning]
      minimum_tier: 2
    documentation_writer:
      required_capabilities: [documentation]
      minimum_tier: 1
    documentation_verifier:
      required_capabilities: [documentation, verification]
      minimum_tier: 2
  fallback: cheap-general
  retry:
    preserve_assignment: true
    allow_escalation: false
  host:
    require_application: false
```

`require_application` defaults to `false`. A host may still be configured to require
application for a particular deployment, but portability is the default behavior.

### 7.1 Ranking

Among suitable models, the resolver ranks candidates by:

1. Explicit role override.
2. Required capability coverage.
3. Policy minimum tier.
4. Explicit tier ranking.
5. Context-window sufficiency.
6. Tool compatibility.
7. Cost preference.
8. Stable catalog order as the final tie-breaker.

The exact ranking must be deterministic. A resolver must return the reason for the
selected candidate rather than only the candidate ID.

### 7.2 Overrides

User or run-level overrides may specify a portable model ID per role. Overrides are
validated against the catalog and policy. An override that lacks required capabilities
is rejected unless the policy explicitly permits a warning-only override.

### 7.3 Fallbacks

Fallbacks are explicit and ordered. A fallback may be used when:

- The requested model ID is unavailable.
- The host has no mapping for the resolved model.
- The host rejects the model application.
- A model exceeds the available context window.

The selected fallback and reason are recorded. If no valid fallback exists, the phase is
`BLOCKED` rather than silently using the parent model.

### 7.4 Retries and escalation

A retry preserves the original resolved model by default. Escalation is allowed only when
`allow_escalation` is true and the escalation rule identifies:

- The triggering condition.
- The prior model.
- The new model.
- The policy rule authorizing the change.

Every attempt records its own assignment. A verifier failure alone does not authorize
escalation unless the policy says so.

## 8. Assignment Contract

Every delegated call receives a model assignment with this shape:

```yaml
model_assignment:
  requested: reasoning-pro
  resolved: Claude Opus 4.8 (copilot)
  portable_id: reasoning-pro
  role: step-verifier
  source: policy
  fallback: null
  applied: true
  adapter: copilot
  evidence: adapter-confirmed
  runtime_model: Claude Opus 4.8 (copilot)
  rationale: "Independent verification of parser behavior."
  warning: null
```

The fields mean:

- `requested`: ID explicitly requested by policy, user, or agent recommendation.
- `resolved`: host-specific model name or the actual selected runtime model.
- `portable_id`: catalog ID used for validation.
- `role`: stable workflow role, not an agent name.
- `source`: `user`, `policy`, `decomposer`, `orchestrator`, or `fallback`.
- `fallback`: portable ID used after the original request could not be applied.
- `applied`: whether the host confirmed use of the resolved model.
- `adapter`: adapter that handled resolution and application.
- `evidence`: `adapter-confirmed`, `host-reported`, `self-reported`, or `unknown`.
- `runtime_model`: model reported by the host or delegated agent, when available.
- `rationale`: concise selection explanation.
- `warning`: required when application differs from the requested assignment.

The assignment is attached to the delegation input and copied into the resulting handoff.

## 9. Persistence Model

Model data must be persisted at every level required for resumability and auditability.

### 9.1 `run.yaml`

Add:

```yaml
model_routing:
  catalog_source: .agent-work/<run-id>/model-catalog.yaml
  policy_source: .agent-work/<run-id>/model-policy.yaml
  adapter: copilot
  preflight:
    status: passed
    verified_path: materialized-agent
    evidence: adapter-confirmed
    session_id: copilot-session-123
    checked_at: 2026-09-14T12:00:00Z
  catalog_fingerprint: sha256:...
  policy_fingerprint: sha256:...
  override_confirmed: false
  warnings: []
```

The run ledger also records the validated catalog and policy fingerprints, configuration
versions, and whether invocation overrides required user confirmation. The repository
configuration paths remain recorded as provenance, but the copied effective files are the
inputs used for resumption.

### 9.2 `step-index.yaml`

Each step receives role assignments before execution:

```yaml
model_assignments:
  implementer:
    portable_id: coding-standard
    source: decomposer
  verifier:
    portable_id: reasoning-pro
    source: policy
```

The orchestrator replaces recommendations with validated assignments before launching the
step. The original recommendation remains available in the step report for auditability.

### 9.3 Step status

Step status contains the resolved assignment for the current attempt, the application result,
and the attempt history. Previous attempts are append-only records.

### 9.4 Handoffs

`agent-handoff/v1` gains a required `model_assignment` object under `details` for every
delegated role. The object records the exact model used for that attempt, including
fallback and application warnings.

Malformed or missing model evidence is treated like any other malformed handoff and maps
to `BLOCKED`.

### 9.5 Documentation assignments

Documentation assignment files contain separate writer and verifier assignments in YAML
frontmatter. Model assignments do not belong in the Markdown body, which is reserved for
the documentation brief and task-specific instructions. The writer assignment is created
only after verified implementation evidence is available. The verifier assignment is
independent and may use a stronger model.

For example:

```yaml
---
schema: documentation-assignment/v1
model_assignments:
  writer:
    portable_id: documentation-standard
  verifier:
    portable_id: reasoning-pro
---
```

## 10. Adapter Interface

The routing core depends on a host adapter registry. The registry selects exactly one
adapter for the active host and rejects unknown host identifiers before delegation.
Adapters are execution boundaries: the routing core owns policy and assignment decisions;
the adapter owns translation to host-specific configuration and reporting of what the
host actually did.

### 10.1 Adapter lifecycle

Before the implementation run starts, the orchestrator invokes a required adapter
preflight exactly once. The preflight verifies the active host/session's model-selection
mechanism and caches the result in `run.yaml`. If the preflight succeeds, later
delegations use the verified adapter path without repeating host capability or discovery
checks.

The preflight occurs after the effective catalog and policy have been confirmed and copied
under `.agent-work/`, but before plan auditing, decomposition, or implementation begins.
If it fails, the orchestrator follows `require_application`: it blocks before delegation
when application is required, or records a warning and continues in unapplied mode when
application is optional.

After a successful preflight, the orchestrator invokes the adapter for each delegated
call in this order:

1. `resolve()` translates the validated portable assignment into a host request.
2. `apply()` uses the preflight-verified mechanism for the delegated role.
3. `get_runtime_model()` obtains runtime evidence when the host exposes it.
4. The orchestrator records the result before consuming the agent handoff.

The adapter must not select a different portable model during `apply()`. Resolution,
fallback, and escalation happen in the routing core so that policy decisions remain
consistent across hosts. The adapter may report that a host-side fallback occurred, but
the orchestrator must reconcile that result with the configured fallback policy before
continuing.

The preflight result is invalidated only if the run changes host/session, adapter version,
or explicitly changes the adapter configuration. A normal retry does not trigger another
preflight.

### 10.2 Adapter operations

The minimum adapter interface is:

```text
preflight(context) -> AdapterPreflight
resolve(request, catalog_entry) -> Resolution
apply(resolution, delegation) -> ApplicationResult
get_runtime_model() -> RuntimeModel
```

`preflight()` replaces repeated per-delegation capability probing. It verifies the
selection mechanism once and returns the cached adapter capabilities, session identity,
verification evidence, and supported application path.

The conceptual result types are:

```yaml
adapter_capabilities:
  host: copilot
  can_select_model: true
  can_select_per_delegation: false
  can_report_runtime_model: unknown
  supports_ordered_fallbacks: true

adapter_preflight:
  status: passed
  host: copilot
  adapter_version: v1
  session_id: copilot-session-123
  verified_path: materialized-agent
  evidence: adapter-confirmed
  verified_model: Claude Opus 4.8 (copilot)
  checked_at: 2026-09-14T12:00:00Z

resolution:
  portable_id: reasoning-pro
  host_model: Claude Opus 4.8 (copilot)
  host_selector: null
  fallback_portable_id: null
  rationale: "Meets reasoning and verification requirements at tier 3."

application_result:
  applied: false
  runtime_model: unknown
  evidence: unknown
  warning: "Host cannot confirm a runtime override."
  error: null
```

`can_select_model` means that the host has some model-selection mechanism. The stronger
`can_select_per_delegation` flag is required for dynamic routing of individual agents.
`can_report_runtime_model` is one of `yes`, `no`, or `unknown` and controls whether the
adapter may claim deterministic runtime evidence.

### 10.3 Evidence levels

Application results use one of these evidence levels:

- `adapter-confirmed`: the adapter received deterministic host confirmation.
- `host-reported`: the host exposed the runtime model but did not confirm the override.
- `self-reported`: the delegated agent reported the model it observed or was configured
  to use.
- `unknown`: no runtime model evidence was available.

Evidence level and `applied` are separate fields. For example, a host-reported model may
be known while `applied` remains `false` because the host did not confirm the override.
Only `adapter-confirmed` may support the strongest claim that the requested model was
applied. Self-reports are retained for auditability but are lower-confidence evidence.

### 10.4 Application outcomes

Adapters must distinguish these cases:

- Requested model was resolved and applied.
- A valid fallback was resolved and applied.
- The host used its default model because application was unavailable.
- The request was rejected and execution was blocked.

The orchestrator handles outcomes as follows:

| Outcome | `require_application: false` | `require_application: true` |
| --- | --- | --- |
| Requested model applied | Continue | Continue |
| Policy fallback applied | Continue with warning | Continue with warning |
| Default model used, no proof | Continue with warning | Block |
| Adapter rejection | Resolve policy fallback or block | Resolve policy fallback or block |

Every non-requested outcome includes a warning and the exact reason. An adapter error is
not converted into a verification failure and is not retried unless adapter retries are
explicitly enabled by policy.

### 10.5 Host adapter configuration

Host mappings are data, not executable instructions. The adapter validates a mapped host
selector against the host's accepted model syntax before application. An invalid selector
is an adapter rejection, not a reason to pass arbitrary text through to a subprocess or
host API.

The adapter registry should expose a stable host name and adapter version in every result:

```yaml
adapter: copilot
adapter_version: v1
```

This makes resumed runs and historical reports interpretable after adapter behavior
changes. A resumed attempt uses the adapter version recorded for that attempt; it does
not rewrite prior evidence with a newer adapter.

## 11. Copilot Adapter

### 11.1 Supported mechanisms

The Copilot adapter maps portable IDs to Copilot model names and materializes a temporary
custom-agent definition for each delegated attempt. It may use:

- Custom-agent `model` declarations.
- Ordered model fallback declarations.
- Handoff model fields for explicit user-guided transitions.
- Host task or subagent model parameters where the installed host exposes them.

The adapter preflight must distinguish an agent definition's fixed model policy from a
runtime per-delegation override. A fixed model declaration proves only that a role can be
configured with a model; it does not prove that the orchestrator can select a different
model for each call.

### 11.2 Materialized-agent workflow

When direct model selection on the subagent delegation operation is unavailable, the
Copilot adapter uses the custom-agent definition as the model-selection mechanism. The
adapter first verifies this mechanism once during run preflight by creating a probe
profile, confirming discovery, and confirming that the probe can be delegated with its
model frontmatter. The successful preflight result is then cached for the run.

After that one-time check, each attempt:

1. Selects the canonical role file, such as `agents/step-verifier.agent.md`.
2. Parses its frontmatter without changing the role instructions or tools.
3. Resolves the portable model ID to a validated Copilot model identifier.
4. Creates a uniquely named temporary agent definition for the run and attempt.
5. Copies the canonical frontmatter and body into the temporary definition.
6. Replaces only the controlled model-routing fields in the frontmatter.
7. Places the generated file in the same Copilot-discoverable location verified by
  preflight.
8. Delegates to the generated agent by its temporary name.
9. Persists the assignment and generated-profile metadata.
10. Cleans up the generated profile only after the handoff and evidence are persisted.

The generated definition is an execution profile, not a new workflow role. Its name
should include the role, portable model ID, run ID, and attempt:

```text
step-verifier__reasoning-pro__run-001__attempt-1
```

Conceptually, its frontmatter is:

```yaml
---
name: step-verifier__reasoning-pro__run-001__attempt-1
description: "Temporary model-routed Step Verifier."
model:
  - Claude Opus 4.8 (copilot)
tools: [read, search, execute]
user-invocable: false
---
```

The adapter preserves the canonical role's instructions, tools, permissions, and handoff
requirements. It may change only the generated name, model declaration, and description
or other explicitly approved routing metadata. If arbitrary metadata is unsupported,
routing metadata remains in the persisted assignment.

The generated model list contains the selected model only. A frontmatter list is a host
fallback sequence, not a request to use multiple models. If policy permits fallback, the
adapter generates a new attempt profile with the fallback model and records the change.

### 11.3 Discovery and application evidence

Creating a file does not prove that Copilot discovered or used it. The adapter validates
the discovery and model-selection path during preflight, before the run starts. The
preflight establishes that:

- The generated file is in a directory scanned by the active Copilot host.
- The generated agent name is available to the delegation mechanism.
- The active session recognizes the generated definition.
- The model frontmatter is accepted by the host.

Later profiles inherit this verified path. They do not repeat the discovery probe. The
adapter still records the profile name, requested model, resolved model, and any runtime
evidence returned by the delegation.

Deterministic confirmation produces:

```yaml
applied: true
evidence: adapter-confirmed
runtime_model: Claude Opus 4.8 (copilot)
```

If preflight discovery succeeds but model use cannot be confirmed, the adapter records the
run's selection path as unapplied and permits self-report evidence for later attempts:

```yaml
applied: false
evidence: self-reported
warning: "Generated agent was discoverable, but Copilot did not confirm model use."
```

The self-report must include the generated agent name and attempt. It does not cause a
second preflight.

### 11.4 Runtime limitation

The materialized-agent workflow depends on runtime custom-agent discovery. If definitions
are scanned only when the session starts, the adapter must pre-generate the probe profile
and all required role/model profiles before the session starts, use a supported refresh
mechanism during preflight, or report that dynamic application is unavailable before the
run begins.

When unavailable:

```yaml
applied: false
evidence: unknown
warning: "Copilot could not discover the generated model-routed agent."
```

The workflow may continue because `require_application` defaults to `false`. The actual
runtime model is recorded when exposed, then via self-report if available, otherwise as
`unknown`.

### 11.5 Configuration strategy

The implementation uses generated profiles only for active attempts or pre-generated
role/model combinations required by the run. It does not create permanent agent
identities for every catalog entry. `Step Implementer` remains the same workflow role
regardless of the selected model.

When generated profiles are discoverable and honored, the adapter reports
`can_select_per_delegation: true`. When neither generated profiles nor a direct host
parameter supports per-call selection, it reports `false` and follows
`require_application` policy.

## 12. oh-my-pi Adapter

### 12.1 Supported mechanisms

The oh-my-pi adapter maps portable IDs to:

- Explicit per-agent model overrides.
- Configured model roles such as `task`, `slow`, `advisor`, and `smol`.
- Ordered fallback chains.

Per-agent overrides take precedence over agent frontmatter, configured task roles, and
parent-session defaults, subject to the installed version's precedence rules.

The adapter should prefer explicit per-agent model overrides when available. Role aliases
are acceptable only when the adapter records both the requested role and the model that
the host resolved from that role.

### 12.2 Application and reporting

The adapter passes the resolved model or role to the `task` mechanism and records the
runtime model returned by the host. A configured role is not sufficient evidence of the
actual model if the host can resolve the role to a different model; both values should be
recorded where available. If the host does not expose the runtime model, the delegated
agent may self-report it with explicit lower-confidence evidence.

If oh-my-pi rejects the override, the adapter applies the explicit fallback policy and
records the rejection warning. It must not silently use the parent model.

The adapter capability result should report whether the installed oh-my-pi version
supports per-delegation overrides. A configured global task role is not sufficient to
claim dynamic routing for individual workflow roles. This capability is verified once
during run preflight. Later tasks reuse the verified task-override path and do not repeat
the capability probe.

## 13. Pi Support Status

Pi model selection is unsupported in this version of the workflow.

The workflow may still run on Pi using the parent or host-default model, but it must
persist:

```yaml
adapter: pi
applied: false
warning: "Pi does not currently support workflow-managed per-agent model selection."
```

Pi should not be presented as dynamically routed. Future support may use separate Pi
processes or SDK sessions, but that is outside this design and must introduce a dedicated
adapter implementation and application tests.

The current Pi adapter is therefore a deliberate no-op compatibility adapter. It returns
`can_select_model: false`, `can_select_per_delegation: false`, and an unapplied result
with the required warning. It exists so the routing core can report a structured outcome
instead of branching around Pi or pretending that the parent model was selected.

## 14. Failure Handling

### Invalid catalog or policy

Stop before delegation with `BLOCKED`. Report the invalid field, affected role, and
correction required.

### Unknown model ID

Reject the assignment. Use the configured fallback only if it is valid and permitted;
otherwise block the phase.

### Missing capability

Reject a model that does not meet required capabilities unless an explicit warning-only
override exists. Record the unmet capabilities.

### Host mapping unavailable

Resolve a valid fallback if policy allows it. Otherwise block when application is
required, or continue with `applied: false` and a warning when application is optional.

### Adapter failure

Persist the failure before stopping. Do not retry an adapter error as an ordinary
verification repair unless the retry policy explicitly allows adapter retries.

### Preflight failure

Persist the adapter preflight result before stopping or continuing. A failed preflight is
not retried for each delegation. If the host/session or adapter configuration changes,
the orchestrator must start a new preflight and record the new result before continuing.

### Resume after interruption

Reload the persisted assignment for the interrupted attempt. Do not recalculate it from
the current catalog unless the persisted configuration fingerprint no longer matches and
the policy explicitly allows re-resolution. Any re-resolution creates a new attempt and
records the change.

## 15. Compatibility and Migration

Existing runs without model routing fields remain readable:

- Treat absent routing configuration as legacy mode.
- Record the host default as `resolved` when observable.
- Set `applied: false` with a legacy-mode warning when it is not observable.
- Do not retroactively invent assignments for completed attempts.

New runs should require a catalog and policy unless the invocation explicitly requests
legacy mode. Legacy mode must be visible in `run.yaml` and the final report.

Existing agent names and role files remain unchanged. Model selection is an execution
concern and must not create duplicate role definitions for each model.

## 16. Implementation Surface

The first implementation is documentation-first. It defines the portable contracts and
host behavior before any executable routing or adapter integration is added. The first
implementation should update these files:

- `agents/implementation-orchestrator.agent.md`
  - Add catalog loading, validation, assignment ownership, adapter application, and
    persistence rules.
- `agents/step-decomposer.agent.md`
  - Add model recommendations and documentation complexity metadata without final
    documentation model selection.
- `skills/step-index-format/SKILL.md`
  - Define step-level model recommendation and resolved-assignment fields.
- `skills/agent-handoff/SKILL.md`
  - Define the required per-attempt model assignment evidence.
- `README.md`
  - Document catalog configuration, host behavior, and Pi's unsupported status.
- `skills/model-configuration/SKILL.md`
  - Provide the separately invocable guided workflow for creating and editing repository
    catalog and policy files.
- `skills/model-catalog-format/SKILL.md`
  - Define catalog and policy schemas and validation rules.
- `skills/model-routing-adapter/SKILL.md`
  - Define resolution, application, fallback, and reporting contracts.

Executable resolver and adapter code is a subsequent phase. Agent Markdown and skills
remain the portable policy and documentation surface during the first phase.

## 17. Validation Strategy

Validation must cover both routing decisions and persistence.

### Catalog and policy validation

- Accept a valid catalog with supported capabilities.
- Reject duplicate IDs and unknown required fields.
- Reject invalid tiers, costs, context sizes, and fallback references.
- Reject policies that require unsupported capabilities.

### Selection validation

- Select the highest-ranked suitable model deterministically.
- Honor valid user overrides.
- Reject unsuitable overrides.
- Select independent implementer and verifier assignments.
- Select documentation models only after implementation evidence exists.
- Record explicit fallback and escalation reasons.

### Persistence validation

- Persist routing configuration and fingerprints in `run.yaml`.
- Persist assignments in step index, step status, contexts, and handoffs.
- Preserve prior attempt assignments across retries.
- Reject handoffs with missing or contradictory model evidence.
- Resume with the stored assignment rather than silently re-resolving.

### Adapter validation

- Copilot preflight materializes a probe profile from the canonical role without changing
  its body, tools, or permissions, and verifies discovery and model selection once.
- Copilot reuses the verified discovery path and delegates later generated profiles by
  their generated names without repeating the preflight.
- Copilot records unapplied discovery failures accurately and cleans up only after the
  handoff and model evidence are persisted.
- Copilot retries use unique generated profile names and record any model change.
- Copilot records host fallback behavior.
- oh-my-pi passes explicit overrides or configured roles and records the result.
- Pi always reports model selection as unsupported and unapplied.
- Required application failures block; optional application failures warn.

### End-to-end validation

Use a fixture catalog and fake adapters to test:

1. Plan audit and decomposition assignment.
2. Per-step implementation and verification assignment.
3. Documentation writer and verifier assignment after final verification.
4. A retry with the same model.
5. A policy-authorized escalation.
6. A host-unavailable fallback.
7. Resume after interruption.
8. Final report traceability.

## 18. Security and Operational Considerations

Model names and provider identifiers may reveal organizational configuration. Run artifacts
should remain untracked as already required for `.agent-work/`, and access controls should
match the repository's existing workflow artifacts.

The resolver must not interpret model IDs as executable commands. Adapter mappings are
structured values and must be validated before being passed to a host.

Cost and tier fields are routing metadata, not authorization. Hosts remain responsible
for entitlement, quota, and policy enforcement.

## 19. Resolved Decisions

1. The initial catalog and policy are repository files. Invocation overrides are merged,
  displayed as a complete effective configuration, and require user confirmation before
  the run proceeds. Effective copies are stored under `.agent-work/`.
2. `require_application` defaults to `false` for portability.
3. Catalog and policy fingerprints use a normalized hash representation: parse the
  YAML, normalize mappings by key, preserve list order where order is semantic, normalize
  scalar types, and hash canonical serialized data with SHA-256. This avoids equivalent
  YAML formatting changes appearing as configuration changes while preserving ordered
  fallback chains.
4. Subagents may self-report their model when deterministic host signals are unavailable.
  The report must identify self-reported evidence and must not be treated as equivalent
  to adapter-confirmed application.
5. Documentation writer and verifier assignments are persisted in the assignment
  frontmatter block, not in the body.
6. The first implementation documents the contracts and guided configuration workflow;
  executable adapter code follows in a later phase.

The implementation plan may still define the exact repository configuration path, merge
algorithm, and host capability probes, provided they preserve these decisions.

## 20. Acceptance Criteria

The design is ready for implementation when reviewers agree that:

- The orchestrator is the final authority for every model assignment.
- Documentation model selection occurs after implementation evidence is available.
- Recommendations and final assignments are distinguishable in persisted state.
- Every retry records the exact model used and any escalation reason.
- Fallbacks are explicit and auditable.
- Copilot and oh-my-pi have separate adapter responsibilities.
- Pi is documented as unsupported without falsely claiming routing.
- A host cannot be reported as applying a model without application evidence.
- Existing role identities remain stable.
- The proposed validation strategy covers routing, adapters, persistence, and resume.
