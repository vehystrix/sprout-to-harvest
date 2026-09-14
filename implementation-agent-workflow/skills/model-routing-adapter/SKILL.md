---
name: model-routing-adapter
description: "Defines the adapter lifecycle, evidence semantics, and delegation contract for dynamic model routing."
---
# Model Routing Adapter Contract

Use this skill whenever the orchestrator configures, validates, or reads a host adapter that resolves a portable model ID into a host-specific runtime model and reports the actual application result.

## Required lifecycle

The adapter contract is host-neutral. A routing core owns policy decisions; the adapter only translates the chosen portable assignment into a host request and reports what the host actually did.

The required adapter operations are:

```text
preflight(context) -> AdapterPreflight
resolve(request, catalog_entry) -> Resolution
apply(resolution, delegation) -> ApplicationResult
get_runtime_model() -> RuntimeModel
```

The orchestrator invokes `preflight()` exactly once after the effective catalog and policy have been confirmed and copied under `.agent-work/`, and before plan auditing or implementation begins. The result is stored in the run ledger and reused for subsequent delegations unless the host or adapter configuration changes.

The delegation flow is:

1. `resolve()` translates the validated portable assignment into a host request.
2. `apply()` uses the preflight-verified path for the delegated role.
3. `get_runtime_model()` collects runtime evidence when the host exposes it.
4. The orchestrator records the assignment result before consuming the agent handoff.

Adapters must not select a different portable model during `apply()`. Resolution, fallback, and escalation are policy decisions made by the orchestrator. The adapter may detect a host-side fallback or default-model usage, but the orchestrator is responsible for reconciling that with the configured fallback policy and persisted assignment evidence.

## Adapter result types

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

Interpretation:

- `can_select_model` means the host has some model-selection mechanism.
- `can_select_per_delegation` is the stronger flag required for dynamic routing of individual delegated agents.
- `can_report_runtime_model` is one of `yes`, `no`, or `unknown`.
- `adapter_preflight.status` must be `passed` before the host is considered safe for runtime routing.

## Evidence semantics

The adapter reports one of four evidence levels:

- `adapter-confirmed`: the adapter received deterministic host confirmation.
- `host-reported`: the host exposed the runtime model but did not confirm the override.
- `self-reported`: the delegated agent reported the model it observed or was configured to use.
- `unknown`: no runtime model evidence was available.

`evidence` and `applied` are distinct. A host may expose the model in a runtime report while `applied` remains `false`. Only `adapter-confirmed` supports the strongest claim that the requested model was actually applied. Self-reported values remain in the audit trail but are lower-confidence evidence.

## Unsupported host behavior

The workflow must reject unrecognized host identifiers before delegation. An adapter that is not registered for the active host is simply unsupported. The adapter contract therefore distinguishes:

- `adapter-confirmed`
- `host-reported`
- `self-reported`
- `unknown`

An unrecognized or unsupported host must return an explicit unsupported result rather than a dynamic selection claim. That result must be recorded as a warning and kept separate from normal routing evidence.

## Fallback and rejection behavior

Adapters must distinguish these cases:

- Requested model resolved and applied.
- A valid fallback model resolved and applied.
- The host used its default model because application was unavailable.
- The request was rejected and execution was blocked.

The orchestration contract uses the following semantics:

| Outcome | `require_application: false` | `require_application: true` |
| --- | --- | --- |
| Requested model applied | Continue | Continue |
| Policy fallback applied | Continue with warning | Continue with warning |
| Default model used, no proof | Continue with warning | Block |
| Adapter rejection | Resolve policy fallback or block | Resolve policy fallback or block |

Every non-requested outcome must include a warning and the exact reason. Adapter errors are not converted into verification failures and are not retried unless the policy explicitly enables adapter retries.

## Rule requirements for the contract

The skill must define the following required terms explicitly:

- `preflight`
- `resolve()`
- `apply()`
- `get_runtime_model()`
- `adapter-confirmed`
- `host-reported`
- `self-reported`
- `unknown`
- `can_select_per_delegation`
- `require_application`
- fallback outcomes
- unsupported host rejection behavior
- assignment fields and evidence rules

The adapter registry exposes a stable host name and adapter version in every result:

```yaml
adapter: copilot
adapter_version: v1
```

This allows resumed runs and historical reports to remain interpretable after adapter behavior changes. A resumed attempt uses the adapter version recorded for that attempt and does not rewrite earlier evidence.

## Validation checklist

A valid adapter contract must include:

- a `preflight` step before the run begins,
- a `resolve` and `apply` ordering that matches the orchestration flow,
- `get_runtime_model` as a runtime evidence step,
- explicit handling of `adapter-confirmed`, `host-reported`, `self-reported`, and `unknown`,
- `can_select_per_delegation` as the dynamic-routing gate,
- a documented unsupported-host result and no dynamic routing claim,
- exact assignment fields for requested, resolved, applied, runtime, and warning data.
