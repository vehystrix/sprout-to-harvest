---
name: s2h-model-routing-adapter
description: Only use when explicitly invoked
# description: "Catalog-driven delegation guide for dynamic model routing:
#   one-time capability probe, catalog lookup, conditional model field
#   delegation, and channel-keyed evidence recording."
user-invocable: false
disable-model-invocation: true
---
# Model Routing Adapter - Delegation Guide

## Model source resolution

Each of the two model files - `.sprout-to-harvest/model-catalog.json` and
`.sprout-to-harvest/model-policy.json` - is resolved independently, workspace file
first, then the user-level global repository at `~/.sprout-to-harvest/`:

1. The workspace file exists. It is the effective source; the global file
   contributes nothing.
2. The workspace file does not exist and a global file does. The global file
   becomes the effective source for that run.
3. An explicit inclusion applies while the workspace file also exists. The
   workspace entry wins every conflict; the global file contributes only what
   the workspace does not define:
   - Catalog merge: keep all local entries in their declared order and append
     global-only model entries after them; on a duplicate `id`, the local
     entry wins.
   - Policy merge: roles defined locally keep their local definition; absent
     roles are inherited from the global policy. Scalar fields (`fallback`,
     `retry`, `host`) take the local value when present, else the global one.
4. No file exists for a source and no inclusion applies. The effective
   configuration is empty: dynamic model selection is disabled; every delegation
   omits the `model` field with a routing-unavailable warning.

In delegated mode the orchestrator validates, canonicalizes, freezes, and fingerprints
the effective configuration as run copies under `.agent-work/<run-id>/`; readers of the
resolution (orchestrator or decomposer) read those frozen copies. In user mode there is
no freezing: each resolved file is used directly. The merged result is validated exactly
like a single-file configuration before use; validation failures are `BLOCKED` naming
the failing field paths. The fingerprint covers the effective (merged) bytes, not
either source file separately.

## Static tool-surface check

Every delegating agent applies this before any model-bearing delegation, and it is the
only probe step that runs outside delegated mode. Does the active host's delegation tool
expose a per-delegation `model` parameter? If not, record `status: routing-unavailable`,
`mechanism: none`, and pin `evidence_channel` by inspecting the response payload of the
first real delegation - record `self-reported` if that payload has no structured
runtime-model field.

In delegated mode the orchestrator has already run this check; every later delegation
consumes its result from `run.json.model_routing.preflight`. In user mode there is no
per-run probe: the delegating agent applies only this check, which needs no live probes.

## Catalog lookup procedure

To resolve a selected portable ID for delegation, read the run copy of
`.agent-work/<run-id>/model-catalog.json`, find the entry where
`models[].id == selected_portable_id`, and extract its `hosts.<active_host>` value
as the resolved model name. Host names appear only as data values in catalog keys
and in the `adapter:` field, which means "active host identifier." The extracted
value is a selector string, not an executable command.

Example lookup:

```json
{
  "models": [
    {
      "id": "reasoning-pro",
      "hosts": {
        "copilot": "Claude Opus 4.8 (copilot)"
      }
    }
  ],
  "selected_portable_id": "reasoning-pro",
  "active_host": "copilot",
  "resolved_model_name": "Claude Opus 4.8 (copilot)"
}
```

## Delegation

When the probe status is `passed`, pass the resolved model name (or an accepted
role alias for it) as the `model` field on the delegation call. Every passed
delegation also states its effort explicitly: when the selected entry declares
`reasoning_effort`, pass that value on the delegation call alongside `model`;
when no such declaration exists, state no effort - never invent one. When the
probe status is `routing-unavailable`, set no `model` field at all - omit the
field entirely:

```json
{
  "agent": "s2h-StepImplementer",
  "task": "implement step-002",
  "model": "<resolved model name>"
}
```

## Evidence recording after delegation

Record `details.model_assignment` for each delegation, keyed on the probed
`evidence_channel`:

- **tool-reported**: prefer structured runtime-model fields from the delegation
  response payload; record them as `runtime_model`. Tool-reported values support
  applied claims up to `host-reported`.
- **self-reported**: use the subagent's stated runtime model when no tool field
  exists. A self-ID matching the requested model records `runtime_model` from
  self-report with `applied: false` - lower-confidence evidence, kept in the audit trail.

Evidence levels follow `s2h-handoff` and are constrained as follows:

- `adapter-confirmed`: the delegation response payload or a host API
  deterministically confirms the resolved model through a structured confirmation
  field. This is the only level that supports an applied claim; it exists for a run
  only when such a mechanism was observed during the probe.
- `host-reported`: the host exposed a runtime model value without deterministic
  confirmation.
- `self-reported`: the delegated agent reported the model it observed or was
  configured to use.
- `tool-reported`: the delegation response payload reports a runtime model in a
  structured field; it supports applied claims only up to `host-reported`.
- `unknown`: no runtime model evidence was available.

When no confirmation mechanism exists for the run, every assignment records at most
`host-reported` or `self-reported` evidence - never a dynamic-selection claim
backed by `applied: true`.

## Fallback and failure order (unambiguous)

1. **Run-level routing-unavailable.** Probe status `routing-unavailable` means every
   delegation in this run proceeds without a `model` field; each assignment records
   a routing-unavailable warning, `applied: false`, and evidence from whatever channel
   exists. With `require_application: true`, the run is blocked instead of continuing.
2. **Config failure.** The probe passed, but there is no catalog mapping for the
   selected portable ID or, after the single policy-fallback retry below, none for
   its fallback either. After that one retry also lacks a mapping, stop as BLOCKED
   naming the missing entry when `require_application` is true; otherwise continue
   without a model field with `applied: false` and a warning naming the missing
   ID/host mapping. This is a configuration gap, not a host limitation.

Fallback selection rule: when resolution of a role's policy `default` fails under
config failure above, try the policy `fallback` portable ID exactly once; if that
also has no active-host mapping, stop per case 2 (do not silently substitute the
parent model). A retry inherits the prior assignment by default; only explicit
policy-authorized escalation may create a new attempt entry.

## require_application semantics

When `host.require_application` is `true`, block rather than continue whenever the
run cannot demonstrate applied state for an assignment. With no deterministic
confirmation mechanism available - as in every host whose probe found no structured
runtime-model confirmation - this blocks every routed attempt, because none of them
can demonstrate `applied: true`.

## Routing-unavailable host behavior

This path applies to any host where the probe finds no honored per-delegation
selector (for example Pi): record a routing-unavailable warning for every
assignment with `applied: false`, make no dynamic-selection claim, never present
it as dynamically routed, and let continuation be governed by `require_application`.

## Related skills

- `s2h-model-catalog-format`
