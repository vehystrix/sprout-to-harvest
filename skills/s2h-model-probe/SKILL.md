---
name: s2h-model-probe
description: Only use when explicitly invoked
# description: "One-time per-run capability probe run by the orchestrator before any
#   delegation; determines whether the active host honors a per-delegation model
#   parameter and pins the evidence channel for the run."
user-invocable: false
disable-model-invocation: true
---

# Model Probe - One-Time Per-Run Capability Check

The orchestrator runs this probe exactly once per run, before plan auditing begins, after
the effective catalog and policy have been copied under `.agent-work/<run-id>/`. Its
result is cached in `run.json.model_routing.preflight` and reused for every later
delegation of that run. Reusing a cached probe result is valid only while the same host,
session, and effective configuration fingerprint are still in use; if any of those change
on resume, re-run the probe and record a warning.

The static tool-surface check defined by `s2h-model-routing-adapter` runs first; when it
finds no `model` parameter, the live probes below do not run:

1. **Probe P1 (if a `model` parameter exists).** Delegate a trivial self-identification
   task to a candidate model: the cheapest catalog entry with a mapping for the active
   host whose mapped value differs from the current session default; ties on cost break
   by lowest tier, then by catalog order. The "current session default" is the model
   identifier exposed in the host context when visible (for example, the Model line of
   the workstation/system block); if it is not visible, treat it as unknown so no
   candidate is excluded by that rule. The prompt must ask the subagent to state its
   runtime model identifier if one is visible in its context, and MUST NOT name the
   expected model - a self-ID echoing the instruction proves nothing.
2. **Probe P2 (baseline).** Delegate the same self-identification task with no `model`
   request, as a baseline so the orchestrator can tell "host honored the request" from
   "request ignored." If Probe P1 shows the requested model was not honored by the
   response payload or self-ID, the host has an exposed parameter that ignores
   selections: record `status: routing-unavailable` with a warning - never `passed`.
3. **Evidence-channel determination.** Inspect the delegation response payload for a
   structured runtime-model field; its presence pins `evidence_channel: tool-reported`,
   and its absence pins `evidence_channel: self-reported` for the whole run.

If no probe candidate remains (no catalog mapping for the active host, or every mapped
value equals the visible session default), record `status: routing-unavailable` with the
warning "probe inconclusive - no distinct probe target", still run Probe P2 to pin
`evidence_channel`, and set no `model` field on any delegation in this run.

Result values are exactly:

- `status`: `passed | routing-unavailable`
- `mechanism`: `model-parameter | none`
- `evidence_channel`: `tool-reported | self-reported`

Persist the result under `run.json.model_routing.preflight` as a data block, alongside
`catalog_source`, `policy_source`, `adapter` (the active host identifier), fingerprints,
and warnings:

```json
{
  "model_routing": {
    "preflight": {
      "status": "passed",
      "mechanism": "model-parameter",
      "evidence_channel": "tool-reported"
    }
  }
}
```

## Related skills

- `s2h-model-routing-adapter`: owns the static tool-surface check and the per-delegation
  model rules this probe feeds.
- `s2h-model-catalog-format`: defines the catalog entry structure that P1 candidate
  selection reads.
