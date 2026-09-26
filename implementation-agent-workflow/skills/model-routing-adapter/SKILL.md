---
name: model-routing-adapter
description: "Catalog-driven delegation guide for dynamic model routing:
  one-time capability probe, catalog lookup, conditional model field
  delegation, and channel-keyed evidence recording."
---
# Model Routing Adapter - Delegation Guide

## Purpose

This skill is a catalog-driven delegation guide, not an adapter contract with
compiled methods. It contains zero TypeScript extensions, no host bridges, and
no package manifest extensions: the "adapter" is plain documentation telling
the orchestrator how to use whatever per-delegation model-selection mechanism
the active host's delegation tool exposes. No host name may be hardcoded into
routing behavior - whether a run routes models emerges only from its one-time
capability probe outcome, never from an if-branch on the active host identifier.

## Capability probe (exactly once per run)

The orchestrator runs this probe exactly once per run, before plan auditing
begins, after the effective catalog and policy have been copied under
`.agent-work/<run-id>/`. Its result is cached in `run.yaml.model_routing.preflight`
and reused for every later delegation of that run. Reusing a cached probe
result is valid only while the same host, session, and effective configuration
fingerprint are still in use; if any of those change on resume, re-run the
probe and record a warning.

1. **Static tool-surface check first.** Does the active host's delegation tool
   expose a per-delegation `model` parameter? If not, no live probes are needed:
   record `status: routing-unavailable`, `mechanism: none`, and pin
   `evidence_channel` by inspecting the response payload of the first real
   delegation - record `self-reported` if that payload has no structured
   runtime-model field.
2. **Probe P1 (if a `model` parameter exists).** Delegate a trivial
   self-identification task to a candidate model: the cheapest catalog entry with
   a mapping for the active host whose mapped value differs from the current
   session default. The "current session default" is the model identifier
   exposed in the host context when visible (for example, the Model line of the
   workstation/system block); if it is not visible, treat it as unknown so no
   candidate is excluded by that rule. The prompt must ask the subagent to state
   its runtime model identifier if one is visible in its context, and MUST NOT
   name the expected model - a self-ID echoing the instruction proves nothing.
3. **Probe P2 (baseline).** Delegate the same self-identification task with no
   `model` request, as a baseline so the orchestrator can tell "host honored the
   request" from "request ignored." If Probe P1 shows the requested model was
   not honored by the response payload or self-ID, the host has an exposed
   parameter that ignores selections: record `status: routing-unavailable` with
   a warning - never `passed`.
4. **Evidence-channel determination.** Inspect the delegation response payload
   for a structured runtime-model field; its presence pins
   `evidence_channel: tool-reported`, and its absence pins
   `evidence_channel: self-reported` for the whole run.

If no probe candidate remains (no catalog mapping for the active host, or every
mapped value equals the visible session default), record
`status: routing-unavailable` with the warning "probe inconclusive - no distinct
probe target", still run Probe P2 to pin `evidence_channel`, and set no `model`
field on any delegation in this run.

Result values are exactly:

- `status`: `passed | routing-unavailable`
- `mechanism`: `model-parameter | none`
- `evidence_channel`: `tool-reported | self-reported`

Persist the result under `run.yaml.model_routing.preflight` as a data block,
alongside `catalog_source`, `policy_source`, `adapter` (the active host
identifier), fingerprints, and warnings:

```yaml
model_routing:
  preflight:
    status: passed               # or routing-unavailable when no honored selector exists
    mechanism: model-parameter   # or none
    evidence_channel: tool-reported  # or self-reported
```

## Catalog lookup procedure

To resolve a selected portable ID for delegation, read the run copy of
`.agent-work/<run-id>/model-catalog.yaml`, find the entry where
`models[].id == selected_portable_id`, and extract its `hosts.<active_host>` value
as the resolved model name. Host names appear only as data values in catalog keys
and in the `adapter:` field, which means "active host identifier." The extracted
value is a selector string, not an executable command.

Example lookup:

```yaml
# run copy: .agent-work/<run-id>/model-catalog.yaml (excerpt)
models:
  - id: reasoning-pro
    hosts:
      copilot: Claude Opus 4.8 (copilot)

selected_portable_id: reasoning-pro
active_host:          copilot                    # the value of model_routing.adapter
resolved model name:  Claude Opus 4.8 (copilot)
```

## Delegation

When the probe status is `passed`, pass the resolved model name (or an accepted
role alias for it) as the `model` field on the delegation call. When the probe
status is `routing-unavailable`, set no `model` field at all - omit the field
entirely:

```yaml
agent: Step Implementer
task: implement step-002
model: "<resolved model name>"   # present only when probe status is passed
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

Evidence levels in this no-adapters context are defined by
[model-catalog-format](../model-catalog-format/SKILL.md) and constrained as follows:

- `adapter-confirmed`: the delegation response payload or a host API
  deterministically confirms the resolved model through a structured confirmation
  field. This is the only level that supports an applied claim; it exists for a run
  only when such a mechanism was observed during the probe.
- `host-reported`: the host exposed a runtime model value without deterministic
  confirmation.
- `self-reported`: the delegated agent reported the model it observed or was
  configured to use.
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

This path applies to any host where the capability probe finds no honored
per-delegation selector, including Pi. Its delegation tool exposes no per-delegation `model`
parameter, so its static check fails and such runs take this path automatically;
it is an unapplied compatibility adapter and must never be presented as
dynamically routed. Behavior: record a routing-unavailable warning for every
assignment with `applied: false`, make no dynamic-selection claim,
and let continuation be governed by `require_application`.

## Validation checklist

A valid run using this guide shows all of the following:

- one probe result per run persisted in `run.yaml.model_routing.preflight` as a data
  block (`status`, `mechanism`, `evidence_channel`) with cached-result reuse only
  for an unchanged host, session, and configuration fingerprint;
- every delegated role resolved through catalog lookup on the run copy of `model-catalog.yaml`;
- `model` set on delegation calls only when probe status is passed;
- evidence recorded per probed channel, with no dynamic-selection claim while
  routing is unavailable;
- the single policy-fallback retry and BLOCKED semantics above honored.
