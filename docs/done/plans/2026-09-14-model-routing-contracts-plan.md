# Model Routing Contracts Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Define the portable model catalog, routing policy, adapter, assignment, and documentation-assignment contracts required by dynamic model selection.

**Architecture:** Keep model selection data-driven and host-neutral. The catalog and policy describe portable IDs, capabilities, ranking, fallback, and retry rules; adapters resolve and report host behavior without making policy decisions. Persist model evidence as part of every delegated assignment and documentation assignment.

**Tech Stack:** Markdown skill contracts, YAML examples, existing `agent-handoff/v1` and `documentation-assignment/v1` formats, PowerShell and Git checks.

**Spec:** [2026-09-14-dynamic-model-selection-design.md](../specs/2026-09-14-dynamic-model-selection-design.md)

## Global Constraints

- Portable IDs such as `reasoning-pro` and `coding-standard` are the workflow identifiers; provider names remain adapter mappings.
- The orchestrator is the only authority that finalizes assignments.
- `require_application` defaults to `false`.
- Assignment evidence distinguishes requested, resolved, applied, runtime, and warning fields.
- Pi remains an unapplied compatibility adapter and must never be presented as dynamically routed.
- Effective run configuration belongs under `.agent-work/<run-id>/`; repository configuration remains outside that directory.
- Documentation assignments keep model assignments in YAML frontmatter, not the Markdown body.

---

### Task 1: Define catalog and policy schemas

**Files:**
- Create: `skills/model-catalog-format/SKILL.md`
- Test: `skills/model-catalog-format/SKILL.md` (structural review; no executable test harness exists)

**Interfaces:**
- Consumes: the catalog, policy, capability vocabulary, ranking, override, fallback, retry, fingerprint, and legacy rules in sections 6, 7, 14, 15, and 19 of the design.
- Produces: a standalone schema skill defining repository configuration files, required fields, allowed values, merge semantics, validation errors, and normalized fingerprint behavior for later orchestrator work.

- [ ] **Step 1: Write the schema checklist first**

Record the required sections in the skill: file locations, catalog entry schema, capability vocabulary, policy schema, role names, fallback chains, override merge rules, validation rules, normalized SHA-256 fingerprint rules, and legacy-mode behavior.

- [ ] **Step 2: Run the missing-contract check**

Run:

```powershell
rg -n "context_window|require_application|allow_escalation|fingerprint|legacy" skills/model-catalog-format/SKILL.md
```

Expected: FAIL because the file does not exist yet.

- [ ] **Step 3: Write the catalog and policy format**

Define the exact YAML shapes for `models`, `model_policy.roles`, `fallback`, `retry`, and
`host`. State that unknown capabilities, duplicate IDs, invalid numeric values, unknown
fallback references, and unsuitable overrides are invalid. Specify field-level override
merging and canonical normalization: mappings sorted by key, semantically ordered lists
preserved, scalar types normalized, then SHA-256 hashed.

- [ ] **Step 4: Validate the contract text**

Run:

```powershell
rg -n "models:|model_policy:|required_capabilities|context_window|require_application|preserve_assignment|allow_escalation|SHA-256|legacy mode" skills/model-catalog-format/SKILL.md
```

Expected: PASS with every required contract term present.

- [ ] **Step 5: Commit**

```bash
git add skills/model-catalog-format/SKILL.md
git commit -m "docs: define model catalog and policy format"
```

### Task 2: Define adapter and assignment contracts

**Files:**
- Create: `skills/model-routing-adapter/SKILL.md`
- Modify: `skills/agent-handoff/SKILL.md`
- Test: `skills/model-routing-adapter/SKILL.md`, `skills/agent-handoff/SKILL.md` (contract review)

**Interfaces:**
- Consumes: Task 1 portable catalog/policy vocabulary and the design's adapter lifecycle and evidence levels.
- Produces: `preflight`, `resolve`, `apply`, and `get_runtime_model` contracts plus a required `details.model_assignment` handoff object for every delegated role.

- [ ] **Step 1: Write the failing contract assertions**

Define the required terms to verify: `preflight`, `resolve`, `apply`, `get_runtime_model`,
`adapter-confirmed`, `host-reported`, `self-reported`, `unknown`, `can_select_per_delegation`,
`require_application`, fallback outcomes, Pi no-op behavior, and assignment fields.

- [ ] **Step 2: Run the missing-contract check**

Run:

```powershell
rg -n "preflight|model_assignment|adapter-confirmed|can_select_per_delegation" skills/model-routing-adapter/SKILL.md skills/agent-handoff/SKILL.md
```

Expected: FAIL for the new adapter skill and missing assignment fields.

- [ ] **Step 3: Define the adapter skill**

Document the registry, one-time preflight, adapter result types, resolution/application
ordering, evidence semantics, host mapping validation, fallback reconciliation, adapter
versioning, Copilot materialized-agent behavior, oh-my-pi per-delegation behavior, and Pi's
explicit unsupported result. Make clear that adapters cannot choose a different portable
model during `apply()`.

- [ ] **Step 4: Extend the handoff contract**

Add a required `details.model_assignment` example and rules covering `requested`,
`resolved`, `portable_id`, `role`, `source`, `fallback`, `applied`, `adapter`,
`evidence`, `runtime_model`, `rationale`, and `warning`. Require contradictory or missing
model evidence to be treated as `BLOCKED`, while preserving lower-confidence self-reporting.

- [ ] **Step 5: Validate both contracts**

Run:

```powershell
rg -n "preflight|resolve\(|apply\(|get_runtime_model|adapter-confirmed|host-reported|self-reported|can_select_per_delegation|Pi|model_assignment|runtime_model|warning" skills/model-routing-adapter/SKILL.md skills/agent-handoff/SKILL.md
```

Expected: PASS with all lifecycle, evidence, unsupported-host, and assignment terms present.

- [ ] **Step 6: Commit**

```bash
git add skills/model-routing-adapter/SKILL.md skills/agent-handoff/SKILL.md
git commit -m "docs: define model routing and assignment contracts"
```

### Task 3: Extend documentation assignment evidence

**Files:**
- Modify: `skills/documentation-assignment-format/SKILL.md`
- Test: `skills/documentation-assignment-format/SKILL.md` (frontmatter contract review)

**Interfaces:**
- Consumes: Task 2 assignment contract and the existing `documentation-assignment/v1` template.
- Produces: a frontmatter contract with independent writer and verifier model assignments created only after verified implementation evidence.

- [ ] **Step 1: Write the failing assertion**

Require the example frontmatter to contain `model_assignments.writer.portable_id` and
`model_assignments.verifier.portable_id`, while keeping the body dedicated to documentation
scope and verified facts.

- [ ] **Step 2: Run the missing-field check**

Run:

```powershell
rg -n "model_assignments|portable_id|writer|verifier" skills/documentation-assignment-format/SKILL.md
```

Expected: FAIL or show no complete assignment block before editing.

- [ ] **Step 3: Update the format skill**

Add the assignment frontmatter example, validation rules for independent assignments, and
the timing rule that writer/verifier models are selected only after final implementation
verification. State that model evidence belongs in the assignment metadata, not prose.

- [ ] **Step 4: Validate and commit**

Run:

```powershell
rg -n "model_assignments:|writer:|verifier:|after.*implementation|frontmatter|not.*body" skills/documentation-assignment-format/SKILL.md
```

Expected: PASS.

```bash
git add skills/documentation-assignment-format/SKILL.md
git commit -m "docs: add model assignments to documentation format"
```

## Plan Exit Criteria

- The three new or changed skills agree on portable IDs, assignment fields, evidence levels,
  fallback behavior, and Pi status.
- No workflow role is duplicated per model.
- Plan 2 can reference exact catalog, adapter, and handoff field names without redefining them.
- `git diff --check` passes for the plan's commits.
