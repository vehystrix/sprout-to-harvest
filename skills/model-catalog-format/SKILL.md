---
name: model-catalog-format
description: Only use when explicitly invoked
# description: "Defines the repository model catalog and routing policy schema for model selection."
user-invocable: false
disable-model-invocation: true
---
# Model Catalog and Policy Format

Use this skill whenever the orchestrator or a guided config helper writes
or edits the repository-level model catalog and policy. These files are
configuration inputs to the workflow, not runtime state, and they stay
outside `.agent-work/` until the orchestrator copies and validates the
effective run versions.

## File locations

The repository normally stores the canonical files under:

```text
.implementation-agent/model-catalog.yaml
.implementation-agent/model-policy.yaml
```

The effective run copies live under:

```text
.agent-work/<run-id>/model-catalog.yaml
.agent-work/<run-id>/model-policy.yaml
```

The effective copies are the authoritative runtime inputs. Repository
files remain the source of truth for version control and resumed runs; the
run copies are the validated configuration that was confirmed for that
run.

## Catalog entry schema

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
      omp: anthropic/claude-opus-4-8
```

Each catalog entry must satisfy these requirements:

- `id` is a unique portable model identifier.
- `capabilities` is a normalized list of names from the capability vocabulary.
- `tier` is a positive integer; larger values indicate stronger default suitability.
- `cost` is a policy-comparable classification such as `low`, `medium`, or `high`.
- `context_window` is the maximum supported token window.
- `tools` preserves the required or supported host tools for this model.
- `hosts` is optional and maps supported hosts to host-specific selector strings.

Unknown capabilities are invalid unless the format explicitly supports a
namespaced extension. Duplicate model IDs, missing required fields,
invalid numeric values, and unsupported host mapping values are invalid.

## Capability vocabulary

The initial portable capability vocabulary is:

```yaml
capabilities:
  - general
  - orchestration
  - reasoning
  - planning
  - coding
  - testing
  - verification
  - documentation
  - large-context
```

The vocabulary is the contract used by policy matching and validation.
Names are stored in normalized lowercase form and are not treated as
free-form text. Catalog entries may extend the vocabulary only through
an explicit namespace policy; otherwise the value is invalid.

## Policy schema

```yaml
model_policy:
  roles:
    plan_auditor:
      required_capabilities: [reasoning, planning]
      minimum_tier: 2
      default: reasoning-pro
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

The policy defines the role defaults, suitability requirements, fallback
behavior, retry semantics, and host application requirements. It is not a
host registry, and it does not change runtime behavior without
orchestration validation.

## Required fields and semantic rules

- `model_policy.roles.<role>.required_capabilities` is mandatory for each supported role.
- `minimum_tier` is a positive integer or `null` when not enforced.
- Each supported role definition may include an optional `default`
  portable ID naming the primary candidate for that role. A declared
  `default` must exist in the catalog and satisfy the role's own
  `required_capabilities` and `minimum_tier`; it is overridable only by
  a validated decomposer recommendation or user override.
- `fallback` is a portable model ID that must exist in the catalog, or be
  explicitly marked as a child fallback alias.
- `retry.preserve_assignment` must be a boolean; `true` preserves the
  original attempt assignment by default.
- `retry.allow_escalation` must be a boolean; `false` blocks policy
  escalation unless an explicit rule authorizes it.
- `host.require_application` defaults to `false` and is used only when the
  host cannot or should not silently proceed without confirmation.

The workflow must reject unknown fallback references, unsuitable role
overrides, invalid role names, missing capability coverage, and values
that would produce a non-deterministic ranking.

## Override merge and validation rules

Invocation overrides may change individual catalog entries or policy
fields. The orchestrator must merge them by field-level semantics instead
of replacing unrelated sections. The merge behavior is:

1. Mappings are sorted by key for canonical output.
2. Lists retain their semantic order when they are significant (for
   example, capability order or fallback order).
3. Scalar types are normalized before hashing or validation.
4. The merged result is serialized and hashed using a canonicalized SHA-256 representation.

The canonical representation is deterministic: equivalent YAML is
normalized to a stable byte sequence before hashing. The workflow
calculates a normalized fingerprint in the form `sha256:<hex>` for both
catalog and policy. The exact hash is not user-facing behavior; it is
evidence for resume and auditability.

Invalid overrides include:

- a portable model ID not present in the catalog,
- a model override that fails `required_capabilities`,
- a host mapping that is incompatible with the active host,
- a fallback chain that references a missing or recursive ID,
- an override that replaces the entire policy instead of updating its intended field.

## Legacy mode behavior

Legacy mode remains a compatibility option and is treated as an explicit
compatibility path, not as a dynamic routing strategy. In legacy mode, the
orchestrator may preserve older selectors or compatibility rules when a
host requires them, but the portable catalog and policy remain
authoritative. A legacy configuration is invalid if it contradicts the
routing contract or produces a non-portable assignment.

## Validation checklist

A valid model catalog and policy must contain all of the following terms
in a structured way:

- `models:` and `model_policy:` at the top level.
- `required_capabilities` for each role definition.
- `context_window` on each catalog entry.
- `require_application` under the host policy.
- `preserve_assignment` and `allow_escalation` under retry rules.
- a deterministic `SHA-256` fingerprint calculation and canonicalized output.
- explicit `legacy mode` handling when compatibility behavior is used.

`model_policy` is the authoritative policy contract. The catalog and
policy schema remain stable across hosts; each host's entry in `hosts`
translates the selected portable ID to a host-specific model name without
changing the routing policy itself.
