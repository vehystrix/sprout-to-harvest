# Model Routing Simplified Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the two compiled adapter plans (each using a TypeScript host bridge and package extensions) with a pure config-and-documentation approach that uses zero TypeScript extensions. Host behavior is not hardcoded per host name: a one-time capability probe per run determines whether the active host's delegation tool exposes a per-delegation model selector, which mechanism applies, and whether evidence for this session must come from the delegation response payload (tool-reported) or subagent self-identification (self-reported). The "adapter" is therefore plain documentation of how to resolve portable IDs via catalog lookup and delegate with `model` set when — and only when — the probe confirms it.

**Architecture:** Keep model selection data-driven and host-neutral. Catalog YAML maps portable IDs to host-specific selectors; policy YAML defines role requirements (including a per-role `default`), fallback chains, retry rules, and `require_application`. The orchestrator:
1. reads both files for the run,
2. runs a one-time capability probe before plan audit that establishes whether per-delegation model selection works on the active host, which mechanism exposes it, and which evidence channel applies,
3. when confirmed, selects a portable ID per policy for each delegation, resolves the host selector from the catalog, sets `model` on the delegation call, and records evidence afterwards,
4. when not confirmed, delegates without `model`, records routing-unavailable warnings and `applied: false`, and makes no dynamic-routing claim.

No compiled code, no host bridges, no package extensions, no adapter lifecycle methods. The probe is plain skill instructions executed by the orchestrator with ordinary delegations. Hosts whose only model-selection path would be custom-agent profile materialization are out of scope for this release; they report routing-unavailable until a later plan reintroduces that mechanism.

**Tech Stack:** YAML configuration files (bundled as templates), Markdown skill documentation, agent instruction text, PowerShell and Git validation checks. Zero TypeScript, zero compiled adapters.

**Spec:** [2026-09-14-dynamic-model-selection-design.md](../specs/2026-09-14-dynamic-model-selection-design.md)

**Prerequisites:** Complete [Model Routing Contracts Implementation Plan](2026-09-14-model-routing-contracts-plan.md) first for the portable ID vocabulary, evidence levels, and assignment field contract. The contracts define what the data *looks like*; this plan defines how to *use* it without compiled adapters.
**Working directory:** All verification and Git commands in this plan run from the bundle root (the repository root), so every path below is relative to that directory.

## Global Constraints

- Portable IDs such as `reasoning-pro` and `coding-standard` are the workflow identifiers; provider names remain catalog mappings, never commands.
- The orchestrator is the only authority that finalizes assignments.
- `require_application` defaults to `false`.
- Assignment evidence distinguishes requested, resolved, applied, runtime, and warning fields as defined by the contracts plan.
- No host name may be hardcoded into routing behavior: whether a run routes models must emerge from its capability probe outcome, not from an if-branch on the active host identifier.
- Pi remains an unapplied compatibility adapter and must never be presented as dynamically routed; a run probed on Pi finds no selector and takes the routing-unavailable path automatically.
- The capability probe runs exactly once per run. Its result is cached in `run.yaml.model_routing.preflight`; resumed runs reuse it unless the host, session, or configuration fingerprint changes.
- Under this design, `adapter-confirmed` evidence exists only when the delegation response payload or a host API deterministically confirms the resolved model (structured confirmation field). Everything else is at most `host-reported` or `self-reported`. When no confirmation mechanism exists for the run, `require_application: true` blocks instead of continuing.
- Effective run configuration belongs under `.agent-work/<run-id>/`; repository configuration remains outside that directory.
- Documentation assignments keep model assignments in YAML frontmatter, not the Markdown body.
- **Zero TypeScript extensions:** no compiled adapters, no host bridges, no package manifest extensions, no `src/*/` adapter directories. The entire system is YAML config + Markdown documentation + agent instructions + one-time probe delegations.

---

### Task 1: Create catalog and policy YAML templates

**Files:**
- Create: `skills/model-routing-templates/model-catalog-template.yaml`
- Create: `skills/model-routing-templates/model-policy-template.yaml`
- Test: structural review of both files (no executable test harness exists)

**Interfaces:**
- Consumes: the catalog entry schema and policy schema from [model-catalog-format](../../skills/model-catalog-format/SKILL.md), including the optional per-role `default` field documented in Task 4.
- Produces: two ready-to-use YAML template files whose entries satisfy every workflow role's capability and tier requirements, with clear comments explaining each field, placement instructions, and host mappings that are data values — not executable commands.

- [ ] **Step 1: Define the catalog template**

Write `model-catalog-template.yaml` containing a complete `models:` top-level list covering all six workflow role requirement profiles. At least these example entries:
- `reasoning-pro`: capabilities `[reasoning, planning, verification]`, tier 3, cost high, context_window 200000, tools `[read, search, edit, execute]`, hosts `{copilot: "Claude Opus 4.8 (copilot)"}` — serves `plan_auditor`, `step_decomposer`, and `verifier`.
- `coding-standard`: capabilities `[coding, testing]`, tier 1, cost medium, context_window 128000, tools `[read, search, edit, execute]`, hosts `{copilot: "Code Model (copilot)"}` — serves `implementer`.
- `doc-verification`: capabilities `[documentation, verification]`, tier 2, cost medium, context_window 128000, tools `[read, search, edit]`, hosts `{copilot: "Claude Sonnet 4.5 (copilot)"}` — serves `documentation_verifier`; without a tier ≥ 2 entry carrying both capabilities that role would be unsatisfiable.
- `documentation-standard`: capabilities `[documentation]`, tier 1, cost low, context_window 64000, tools `[read, search, edit]`, hosts `{copilot: "Code Model (copilot)"}` — serves `documentation_writer`.
- `cheap-general`: capabilities `[general]`, tier 0, cost low, context_window 64000, tools `[read, search]`, hosts `{copilot: "Haiku (copilot)"}` — the policy fallback target.

Add comment annotations above the file describing where to place it (repository-level `<repo>/.implementation-agent/model-catalog.yaml`, version-controlled; effective run copies live under `.agent-work/<run-id>/`), which fields are required, how to add new entries, that host selectors are data values — not executable commands — and that host mappings are declared for each host that should support per-delegation model selection; a missing key is a valid state whose runs take the routing-unavailable path.

- [ ] **Step 2: Define the policy template**

Write `model-policy-template.yaml` containing a complete `model_policy:` block with:
- `roles:` mapping each workflow role (`plan_auditor`, `step_decomposer`, `implementer`, `verifier`, `documentation_writer`, `documentation_verifier`) to `required_capabilities`, `minimum_tier`, and a `default` portable ID. Example defaults: `plan_auditor → reasoning-pro`, `step_decomposer → reasoning-pro`, `implementer → coding-standard`, `verifier → reasoning-pro`, `documentation_writer → documentation-standard`, `documentation_verifier → doc-verification`.
- `fallback: cheap-general`
- `retry: { preserve_assignment: true, allow_escalation: false }`
- `host: { require_application: false }`

Add comment annotations describing each role requirement, the meaning of `default` (the primary candidate for that role; it must exist in the catalog and satisfy the role's own `required_capabilities` and `minimum_tier`; decomposer recommendations may replace it only when they pass the same validation), the fallback resolution rule, retry semantics (preserve by default; escalation requires explicit policy approval), and host-level `require_application`.

- [ ] **Step 3: Validate template structure**

Run PowerShell checks to confirm both files contain their required top-level keys, all five catalog IDs, per-role defaults, and comment documentation:

```powershell
rg -n "^models:" skills/model-routing-templates/model-catalog-template.yaml
rg -n "reasoning-pro|coding-standard|doc-verification|documentation-standard|cheap-general" skills/model-routing-templates/model-catalog-template.yaml
rg -n "^model_policy:" skills/model-routing-templates/model-policy-template.yaml
rg -n "required_capabilities|minimum_tier|default:|fallback:|preserve_assignment|allow_escalation|require_application" skills/model-routing-templates/model-policy-template.yaml
```

Expected: PASS — all required keys, entry IDs, and comment annotations present.

- [ ] **Step 4: Commit**

```bash
git add skills/model-routing-templates/
git commit -m "docs: add model catalog and policy YAML templates"
```

### Task 2: Rewrite the model-routing-adapter skill as plain documentation with a capability probe

**Files:**
- Delete: `skills/model-routing-adapter/SKILL.md` (replaced by the new doc-only version)
- Create: `skills/model-routing-adapter/SKILL.md` (rewritten — capability probe + catalog lookup + delegation guide, no adapter lifecycle)
- Test: structural review of rewritten skill

**Interfaces:**
- Consumes: the portable ID vocabulary, evidence levels, and assignment fields from Plan 1 (contracts), plus the Task 1 templates.
- Produces: a plain-documentation skill that defines the one-time capability probe, how to resolve a portable ID via catalog YAML lookup, when to delegate with `model` set on the delegation call, how to record evidence keyed on the probed evidence channel, and the routing-unavailable path for hosts without an exposed selector. No preflight/resolve/apply/get_runtime_model methods, no host-name if-branches.

- [ ] **Step 1: Define the required sections for the rewritten skill**

The rewritten skill must contain these explicit sections:
- Purpose: catalog-driven delegation documentation (no compiled code); the "adapter" is instructions telling the orchestrator how to use whatever model-selection mechanism the active host's delegation tool exposes.
- Capability probe (exactly once per run):
  - Static check first: does the active host's delegation tool expose a per-delegation `model` parameter? If not, record `status: routing-unavailable`, `mechanism: none`, and pin `evidence_channel` by inspecting the first real delegation's response payload — record `self-reported` if no structured runtime-model field is present. No live probes needed.
  - If it does: **Probe P1** — delegate a trivial self-identification task requesting a candidate model: the cheapest catalog entry with a mapping for the active host whose mapped value differs from the current session default. The "current session default" is the model identifier exposed in the host context when visible (for example, the Model line of the workstation/system block); if it is not visible, treat it as unknown so no candidate is excluded by that rule. The prompt must ask the subagent to state its runtime model identifier if one is visible in context, and MUST NOT name the expected model (self-ID echoing the instruction proves nothing).
  - **Probe P2** — same self-identification task with no request, as a baseline so the orchestrator can tell "host honored the request" from "request ignored."
  - Inspect the delegation response payload for a structured runtime-model field; that pins `evidence_channel: tool-reported | self-reported` for the whole run.
  - If no candidate remains (no mapping for the active host, or every mapped value equals the visible session default), record `status: routing-unavailable` with warning "probe inconclusive — no distinct probe target", still run Probe P2 to pin `evidence_channel`, and set no `model` field on any delegation.
  - Result values: `status: passed | routing-unavailable`; `mechanism: model-parameter | none`; `evidence_channel: tool-reported | self-reported`. A host with an exposed parameter that ignores selections is `routing-unavailable` with a warning, not `passed`.
- How to resolve: read the run copy of `model-catalog.yaml` → find entry by `id` → look up `hosts.<active_host>` for the resolved model name. Host names appear only as data values in the catalog keys and in the `adapter:` field meaning "active host identifier."
- Delegation: when probe status is `passed`, pass the resolved model name (or an accepted role alias) as the `model` field on the delegation call; when `routing-unavailable`, set no `model` field.
- Evidence recording keyed on `evidence_channel`: tool-reported runtime values record `runtime_model` and support applied claims up to `host-reported`; a deterministic structured confirmation (delegation response or host API) is what makes evidence `adapter-confirmed`. Self-ID matching the request records `runtime_model` from self-report with `applied: false` — lower confidence, kept in the audit trail.
- Evidence levels: `adapter-confirmed`, `host-reported`, `self-reported`, `unknown`, each defined for the no-adapters context per Global Constraints above.
- Fallback and failure order (unambiguous):
  1. Run-level: probe status `routing-unavailable` → every delegation proceeds without `model`; each assignment records a routing-unavailable warning, `applied: false`, evidence from whatever channel exists; with `require_application: true` the run is blocked instead.
  2. Config failure (probe passed but no catalog mapping for the selected ID or its policy fallback): after the single policy-fallback retry also lacks a mapping, stop as BLOCKED naming the missing entry when `require_application` is true; otherwise continue without a model field with `applied: false` and a warning naming the missing ID/host mapping — this is a configuration gap, not a host limitation.
- Fallback selection rule: when resolution of a role's `default` fails under config failure above, try the policy `fallback` portable ID once; if that also has no mapping, stop per case 2 (do not silently substitute the parent model).
- `require_application`: block rather than continue when the run cannot demonstrate applied state for an assignment; with no confirmation mechanism available, this blocks every routed attempt.
- Routing-unavailable hosts: generic section covering any host where the probe finds no honored selector (including Pi) — warning recorded, no dynamic-selection claim, continuation governed by `require_application`.

- [ ] **Step 2: Delete the old adapter skill**

Remove the existing compiled-adapter-contract version:

```bash
git rm skills/model-routing-adapter/SKILL.md
```

Expected: file removed from git tracking.

- [ ] **Step 3: Write the rewritten skill**

Write a new `skills/model-routing-adapter/SKILL.md` that begins with frontmatter (`name: model-routing-adapter`, `description` reflecting the probe-based delegation guide rather than an adapter lifecycle) and covers, in order:

1. **Purpose**: this is a catalog-driven delegation guide, not an adapter contract with compiled methods.
2. **Capability probe procedure**: static tool-surface check → Probe P1 (requested cheap model, self-ID prompt without naming the expected value) → Probe P2 (baseline) → evidence-channel determination; result YAML block to persist under `run.yaml.model_routing.preflight`; reuse-on-resume rule (same host/session/fingerprint).
3. **Catalog lookup procedure**: read run copy of `model-catalog.yaml`, match `models[].id == selected_portable_id`, extract `hosts.<active_host>` — a data value, not a command. Show an example YAML extraction.
4. **Delegation**: set the resolved model name as the `model` parameter on the delegation call when probe status is passed; show an example invocation with `model: "<resolved_model_name>"`. When routing-unavailable, omit the field entirely.
5. **Evidence recording after delegation**: record `details.model_assignment` per host channel — tool-reported payload fields first, self-ID otherwise; define when each evidence level applies in the no-adapters context (per Step 1 above).
6. **Fallback and failure order** exactly as in Step 1 (run-level routing-unavailable path vs config-failure BLOCKED), including the single retry of the policy fallback portable ID.
7. **`require_application` semantics**: block when applied state cannot be demonstrated; note that without a deterministic confirmation mechanism this blocks all routed attempts.
8. **Routing-unavailable host behavior**: warning + no dynamic-routing claim, continuation governed by `require_application`; Pi included implicitly.

- [ ] **Step 4: Validate the rewritten skill**

```powershell
rg -n -i "capability probe|probe p1|probe p2|evidence_channel|mechanism|catalog lookup|hosts\.<active_host>|resolved model name|model.*field|adapter-confirmed|host-reported|self-reported|routing-unavailable|fallback|require_application" skills/model-routing-adapter/SKILL.md
rg -n "preflight\(|resolve\(|apply\(|get_runtime_model" skills/model-routing-adapter/SKILL.md
```

Expected: first grep shows all required documentation sections present; second grep shows zero results — no lifecycle method calls remain (the `preflight:` YAML key in the persisted block is data, not a method).

- [ ] **Step 5: Commit**

```bash
git add skills/model-routing-adapter/SKILL.md
git commit -m "refactor: rewrite model-routing-adapter as probe-based delegation guide"
```

### Task 3: Update orchestrator agent instructions with the capability probe and routing procedure

**Files:**
- Modify: `agents/implementation-orchestrator.agent.md`
- Test: role-instruction review for routing coherence

**Interfaces:**
- Consumes: the rewritten model-routing-adapter skill, the Task 1 templates, and all format skills.
- Produces: orchestrator instructions where step 2 runs the capability probe once per run, step 7 follows catalog-read → portable-select → catalog-resolve → conditional delegate-with-model → evidence-record, and the Rules section contains no adapter lifecycle references.

- [ ] **Step 1: Update the Required skills list**

In the `## Required skills` section, update the model-related skill line so it reads that `model-routing-adapter` is now a config-only probe + catalog-based delegation guide (no compiled adapters), while keeping `model-catalog-format` and the run/step ledger format references.

- [ ] **Step 2: Rewrite rule lines 36 and 38, and adjust line 51**

Replace the existing Rules bullets that reference adapter preflight with probe-based wording (keep surrounding rules unchanged):
- The catalog/policy confirmation rule becomes: confirm the effective model catalog and policy, copy them under `.agent-work/<run-id>/`, run the capability probe exactly once per run, calculate SHA-256 fingerprints, and record `model_routing` in `run.yaml` with `catalog_source`, `policy_source`, `adapter` (the active host identifier), `preflight` (probe result: `status`, `mechanism`, `evidence_channel`), `catalog_fingerprint`, `policy_fingerprint`, `override_confirmed`, and `warnings`.
- The central-routing-path rule becomes: validate IDs against the catalog; select a portable ID from the role's policy `default` (decomposer recommendations may replace it only when they pass `required_capabilities` + `minimum_tier` validation); resolve via `hosts.<active_host>`; delegate with `model` set only when probe status is passed, otherwise without it plus a routing-unavailable warning; persist the assignment before delegation and the application result/evidence after.
- The `require_application` rule becomes: if the host requires confirmation and the run's evidence cannot demonstrate applied state (no deterministic host/tool confirmation), block rather than silently continuing — remove all references to "the adapter."

- [ ] **Step 3: Replace step 2 (configuration confirmation) with probe-including procedure**

Replace the existing step 2 text with:
1. Load effective catalog and policy (repository files, merged overrides confirmed as required), canonicalize, copy under `.agent-work/<run-id>/`, calculate `sha256:` fingerprints.
2. Run the capability probe exactly once per the model-routing-adapter skill: static check of the delegation tool surface for a per-delegation `model` parameter; if absent, record `status: routing-unavailable`, `mechanism: none`, and pin `evidence_channel` from the first real delegation's response payload (record `self-reported` if no structured runtime-model field is present); if present, run Probe P1 (a candidate cheap catalog entry differing from the current session default) and Probe P2 (baseline without request); if no distinct candidate exists, record `status: routing-unavailable` with a "probe inconclusive — no distinct probe target" warning, run only Probe P2 to pin `evidence_channel`, and set no model field on any delegation; inspect response payloads to pin `evidence_channel`.
3. Persist `model_routing` in `run.yaml`: `catalog_source`, `policy_source`, `adapter` (active host identifier), `preflight: { status, mechanism, evidence_channel }`, fingerprints, `override_confirmed`, and warnings including any routing-unavailable warning.
4. If probe status is `routing-unavailable` and `require_application` is true, persist `blocked` and stop; otherwise continue — every later delegation omits the `model` field and records a routing-unavailable warning with `applied: false`.

No preflight method exists; this procedure is the capability check.

- [ ] **Step 4: Replace step 7 (assignment resolution) with the catalog-based procedure**

Replace "Resolve and apply the step assignment" with:
1. Load the effective catalog and policy from `.agent-work/<run-id>/`.
2. Evaluate role requirements (`required_capabilities`, `minimum_tier`) for the current delegation.
3. Select a portable ID: the role's policy `default`; a decomposer recommendation may replace it only when it satisfies the same validation; record the selection source.
4. Resolve the host selector by looking up `models[].id == selected_portable_id`, then extract `hosts.<active_host>`. If the mapping is missing, try the policy `fallback` portable ID once; if that also lacks a mapping, stop as BLOCKED naming the missing entry when `require_application` is true, otherwise continue without a model field with `applied: false` and a warning naming the missing entry (config failure).
5. Persist the pre-delegation assignment: requested portable ID, resolved model name, selection source, fallback used (if any).
6. Delegate: when probe status is passed, set `model` to the resolved value on the delegation call; when routing-unavailable, set no `model` field and record a routing-unavailable warning with `applied: false`.
7. After delegation, persist the application result per probed evidence channel: runtime model (tool-reported payload first, self-ID otherwise), `evidence`, and any warnings. Never claim dynamic selection when status is routing-unavailable.

The new text must make it clear that no preflight step and no method-based resolve or apply lifecycle exist — the orchestrator reads YAML directly, probes once, and delegates with the `model` field only when confirmed.

- [ ] **Step 5: Add the probe-gate rule**

Add a new rule in the `## Rules` section:
```
Per-delegation model selection is used only when this run's capability probe status is passed. When it is routing-unavailable, set no model field on any delegation and record a routing-unavailable warning with applied false for every assignment. No host name may hardcode either outcome.
```

- [ ] **Step 6: Validate orchestrator consistency**

```powershell
rg -n -i "capability probe|probe p1|probe p2|evidence_channel|routing-unavailable|model_routing|catalog_source|required_capabilities|minimum_tier|default|fallback|hosts\.<active_host>|resolved" agents/implementation-orchestrator.agent.md
rg -n "preflight\(|resolve\(|apply\(|get_runtime_model|invoke the adapter|run the adapter" agents/implementation-orchestrator.agent.md
```

Expected: first grep shows all new routing procedure terms present; second grep shows zero results — old lifecycle method calls and stale "adapter invocation" prose are gone.

- [ ] **Step 7: Commit**

```bash
git add agents/implementation-orchestrator.agent.md
git commit -m "docs: replace adapter lifecycle with capability probe and catalog routing in orchestrator"
```

### Task 4: Align format skills, schema skill, and remaining stale references

**Files:**
- Modify: `skills/run-ledger-format/SKILL.md` — restructure the `model_routing.preflight` block as data (probe result), clarify `adapter` means the active host identifier, and replace the "Invoke adapter preflight() exactly once per run" write-rule bullet with probe wording.
- Modify: `skills/model-catalog-format/SKILL.md` — document the optional per-role `default` field used by policy selection and templates.
- Review: `skills/step-index-format/SKILL.md` and `skills/step-status-format/SKILL.md` — verify consistency with host-identifier semantics (minor or no changes; expected clean).
- Review: `skills/documentation-assignment-format/SKILL.md` — already has `model_assignments.writer.verifier` with `portable_id`. No changes required.
- Modify: `skills/model-configuration/SKILL.md` — remove the sentence asserting that validation does not call `preflight()`, `resolve()`, `apply()`, or `get_runtime_model()`; replace with a note that runtime confirmation is handled by the orchestrator's one-time capability probe and no lifecycle methods exist.
- Modify: `agents/step-decomposer.agent.md` — fix the stale "the orchestrator resolves final model assignments after adapter preflight" sentence to reference the capability probe instead.

**Interfaces:**
- Consumes: the rewritten adapter skill, updated orchestrator procedure, and Task 1 templates.
- Produces: format skills and supporting instructions that consistently refer to catalog-driven resolution and the probe, with `adapter` fields meaning the active host name (e.g., `copilot`) — not a compiled module — and zero remaining lifecycle method references anywhere in the bundle.

- [ ] **Step 1: Update run-ledger-format**

In the `model_routing:` example, change:
```yaml
  adapter: copilot
  preflight: passed
```
to:
```yaml
  adapter: copilot                # active host identifier (the hosts.<...> key used)
  preflight:
    status: passed               # or routing-unavailable when no honored selector exists
    mechanism: model-parameter   # or none
    evidence_channel: tool-reported  # or self-reported
```

Update the prose describing `model_routing` to state that `catalog_source` and `policy_source` identify the YAML config files used for this run, `adapter` is the active host identifier (the value appearing under `hosts.*` in the catalog), and the `preflight` block records the one-time capability probe result: whether a per-delegation selector was confirmed, which mechanism exposes it, and which evidence channel applies. Replace the write-rule bullet "Invoke adapter `preflight()` exactly once per run and persist the result..." with: "Run the capability probe exactly once per run using the model-routing-adapter procedure and persist its result in `model_routing.preflight`. Reusing a cached probe result is valid only while the same host, session, and effective configuration fingerprint are still in use; otherwise record a warning."

- [ ] **Step 2: Document per-role default in model-catalog-format**

In the policy schema section of `skills/model-catalog-format/SKILL.md`, add that each supported role definition may include an optional `default` portable ID naming the primary candidate for that role. Add validation rules: a declared `default` must exist in the catalog and satisfy the role's own `required_capabilities` and `minimum_tier`; it is overridable only by a validated decomposer recommendation or user override. Keep the existing schema example consistent (add one `default:` line to the example policy).

- [ ] **Step 3: Fix stale references in model-configuration and step-decomposer**

In `skills/model-configuration/SKILL.md`, replace the validation-note sentence naming lifecycle method calls with a note that configuration validation is separate from runtime model confirmation, which happens only through the orchestrator's one-time capability probe. In `agents/step-decomposer.agent.md`, change "the orchestrator resolves final model assignments after adapter preflight and policy validation" to reference the capability probe instead of an adapter preflight.

- [ ] **Step 4: Verify no lifecycle references remain**

Run a targeted grep across all touched files:

```powershell
rg -n "preflight\(|resolve\(|apply\(|get_runtime_model|invoke the adapter" skills/run-ledger-format/SKILL.md skills/step-index-format/SKILL.md skills/step-status-format/SKILL.md skills/documentation-assignment-format/SKILL.md skills/model-catalog-format/SKILL.md skills/model-configuration/SKILL.md agents/step-decomposer.agent.md
```

Expected: zero matches — no compiled lifecycle method references or stale "adapter invocation" prose remain. (The `preflight:` YAML key and the word adapter as a host identifier are allowed.) If any match appears, update the relevant file to refer to catalog lookup or the probe instead.

- [ ] **Step 5: Commit format skill updates**

```bash
git add skills/run-ledger-format/SKILL.md skills/model-catalog-format/SKILL.md skills/step-index-format/SKILL.md skills/step-status-format/SKILL.md skills/documentation-assignment-format/SKILL.md skills/model-configuration/SKILL.md agents/step-decomposer.agent.md
git commit -m "docs: align format skills and instructions with probe-based routing"
```

### Task 5: Document the deletion of adapter plans and update references

**Files:**
- Delete: `docs/superpowers/plans/2026-09-14-model-routing-omp-adapter-plan.md`
- Delete: `docs/superpowers/plans/2026-09-14-model-routing-copilot-adapter-plan.md`
- Modify: `README.md` — update the "Model configuration and routing" section to reflect the simplified approach

**Interfaces:**
- Consumes: confirmation that the two adapter plans are superseded.
- Produces: cleaned-up plan directory (two files removed) and an updated README section explaining that model routing uses catalog YAML + per-delegation `model` field delegation gated by a one-time capability probe, with zero compiled adapters.

- [ ] **Step 1: Delete the obsolete adapter plans**

```bash
git rm docs/superpowers/plans/2026-09-14-model-routing-omp-adapter-plan.md
git rm docs/superpowers/plans/2026-09-14-model-routing-copilot-adapter-plan.md
```

Expected: both plans removed from git tracking.

- [ ] **Step 2: Update README model routing section**

In the README's "Model configuration and routing" section, update the subsections:

a) Replace the first two paragraphs of "Host support and scope" — starting respectively with "Copilot and the Oh-My-Pi (omp) adapter have separate responsibilities" and "The Pi harness does not support model selection, so it is intentionally not included in the adapter list." — with a probe-based explanation:
```text
Model delegation uses whatever per-delegation `model` mechanism the active host exposes. A one-time capability probe at run start confirms whether that mechanism works for the session and pins how evidence is obtained (delegation response payload or subagent self-report). Runs without a confirmed mechanism delegate without a model field and record routing-unavailable warnings; on Pi the static check finds no exposed per-delegation `model` parameter, so such runs take the routing-unavailable path.
```

b) Add a "How it works" paragraph:
```text
The simplified approach uses zero compiled adapters. Model resolution happens entirely through YAML catalog lookup, a one-time capability probe, and per-delegation `model` field delegation:

1. The orchestrator reads the effective run copy `.agent-work/<run-id>/model-catalog.yaml` to map the selected portable ID to a host-specific model name via `hosts.<host>`.
2. A one-time capability probe (a cheap self-identification delegation) confirms whether the active host honors per-delegation model selection and pins the evidence channel for the run.
3. When confirmed, the `model` field is set on each delegation; otherwise no model field is set and warnings are recorded.

No TypeScript, no host bridges, no package extensions. The catalog and policy are pure YAML configuration files that can be edited independently of the workflow code.
```

c) Replace the final paragraph of that section — the one starting "This release establishes the portable contracts, guided configuration, persistence rules..." — with a note that:
```text
This release replaces the original compiled adapter approach with a config-and-documentation model plus a one-time capability probe per run. The TypeScript adapter plans (OMP adapter, Copilot adapter) have been removed. Model routing now operates entirely through catalog YAML, policy YAML, per-delegation `model` fields where the host exposes them, and plain documentation in the model-routing-adapter skill. See [Model Routing Simplified Plan](docs/superpowers/plans/2026-09-16-model-routing-simplified-plan.md) for the complete design.
```

d) Add a migration note:
```text
**Migration from compiled adapters:** If you previously read the OMP adapter plan or Copilot adapter plan, those approaches are replaced. The portable ID vocabulary, evidence levels, and assignment field contracts remain unchanged — only the mechanism changed from TypeScript bridges to catalog YAML lookup + `model` field delegation gated by a one-time capability probe.
```

e) Update the "Runtime evidence" subsection wording so the strongest claim (`adapter-confirmed`) is defined as deterministic host/tool confirmation of the resolved model, note that runs without such confirmation can record at most `host-reported` or `self-reported` evidence, and reword its intro sentence stating that an adapter contract in model-routing-adapter defines these evidence levels to say "the model-routing-adapter delegation guide defines these evidence levels."

- [ ] **Step 3: Validate README consistency**

```powershell
rg -n "capability probe|simplified|config-and-documentation|zero compiled|routing-unavailable|catalog YAML" README.md
rg -n "have separate responsibilities|later executable resolver" README.md
```

Expected: first grep shows updated simplified-approach references present; second grep shows zero matches — old compiled-adapter language is gone.

- [ ] **Step 4: Commit**

```bash
git add README.md
git commit -m "docs: remove TypeScript adapter plans, document probe-based config approach in README"
```

(Note: the two `git rm` commands already ran in Step 1; only `README.md` is staged here so nothing is removed twice.)

---

## Plan Exit Criteria

- The two compiled adapter plan files are deleted; no remaining reference to them exists except in this migration note.
- Two YAML template files (`model-catalog-template.yaml`, `model-policy-template.yaml`) exist with entries satisfying every workflow role's requirement profile — including a tier ≥ 2 entry carrying both `documentation` and `verification` for `documentation_verifier` — per-role `default` IDs, policy fallback/retry/host blocks, and at least one host mapping per catalog entry.
- The `model-routing-adapter` skill is plain documentation: capability probe (static check + Probe P1 + Probe P2, including the inconclusive "no distinct probe target" outcome) → result cached as `preflight { status, mechanism, evidence_channel }` in the run ledger → catalog lookup → conditional delegate-with-model → channel-keyed evidence recording. No compiled lifecycle methods; no host-name if-branches; routing-unavailable path documented generically (Pi included).
- The orchestrator agent instructions run the capability probe exactly once per run before plan audit, gate every `model` field on probe status, use the role `default` plus validated recommendation replacement in step 7, and contain zero old preflight/resolve/apply or "invoke the adapter" references (Rules included).
- Format skills (`run-ledger-format`, `step-index-format`, `step-status-format`, `documentation-assignment-format`), `model-catalog-format` (with documented optional per-role `default`), `model-configuration`, and `agents/step-decomposer.agent.md` contain zero compiled adapter lifecycle method references. The `adapter` field in YAML examples means the active host identifier, and `preflight` is a data block holding probe results.
- README reflects the simplified approach: zero TypeScript, catalog YAML + capability probe + conditional `model` field delegation, updated runtime-evidence wording, migration note from old adapter plans.
- No run may claim dynamic model selection on a host whose capability probe did not pass; routing-unavailable runs record warnings with `applied: false`; Pi is never presented as dynamically routed.
- `git diff --check` passes for all commits in this plan.
