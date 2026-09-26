# Model Routing Orchestration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Integrate validated model assignments into durable run, step, delegation, and orchestration contracts without changing stable workflow role identities.

**Architecture:** The orchestrator loads and freezes effective catalog/policy inputs, performs one adapter preflight, resolves every assignment centrally, and persists assignment evidence before and after delegation. The decomposer may emit recommendations and complexity signals, but only the orchestrator converts them into final assignments.

**Tech Stack:** Markdown agent definitions, YAML state-format contracts, existing workflow roles, and PowerShell/Git validation checks.

**Spec:** [2026-09-14-dynamic-model-selection-design.md](../specs/2026-09-14-dynamic-model-selection-design.md)

**Prerequisite:** Complete [Model Routing Contracts Implementation Plan](2026-09-14-model-routing-contracts-plan.md) first.

## Global Constraints

- Existing role identities remain `Plan Auditor`, `Step Decomposer`, `Step Implementer`, `Step Verifier`, `Documentation Agent`, and `Documentation Verifier`.
- Recommendations and resolved assignments must remain distinguishable.
- A retry preserves the previous assignment unless explicit escalation policy authorizes a new attempt.
- Previous attempt records are append-only.
- The orchestrator persists assignment data before delegation and exact application/evidence after delegation.
- A missing or malformed model assignment in a handoff is `BLOCKED`.
- Documentation model selection occurs only after final implementation verification.

---

### Task 1: Extend run-level routing persistence

**Files:**
- Modify: `skills/run-ledger-format/SKILL.md`
- Test: `skills/run-ledger-format/SKILL.md` (schema review)

**Interfaces:**
- Consumes: `model-catalog-format` and `model-routing-adapter` from Plan 1.
- Produces: a `run.yaml.model_routing` schema containing frozen sources, adapter, preflight, fingerprints, override confirmation, and warnings.

- [ ] **Step 1: Write the failing schema assertions**

Require `catalog_source`, `policy_source`, `adapter`, `preflight`, `catalog_fingerprint`,
`policy_fingerprint`, `override_confirmed`, and `warnings` in the run-level example.

- [ ] **Step 2: Run the missing-field check**

```powershell
rg -n "model_routing|catalog_fingerprint|policy_fingerprint|preflight|override_confirmed" skills/run-ledger-format/SKILL.md
```

Expected: FAIL or show no complete routing block.

- [ ] **Step 3: Add the model-routing block and rules**

Document that effective catalog and policy copies are created under the run directory
before delegation; resumed runs use those copies. Define one-time preflight persistence,
fingerprint provenance, override confirmation, warning persistence, and legacy-mode visibility.

- [ ] **Step 4: Validate and commit**

```powershell
rg -n "model_routing:|catalog_source:|policy_source:|preflight:|catalog_fingerprint:|policy_fingerprint:|override_confirmed:|warnings:" skills/run-ledger-format/SKILL.md
```

Expected: PASS.

```bash
git add skills/run-ledger-format/SKILL.md
git commit -m "docs: persist model routing in run ledger"
```

### Task 2: Extend step recommendation, assignment, and retry state

**Files:**
- Modify: `skills/step-index-format/SKILL.md`
- Modify: `skills/step-status-format/SKILL.md`
- Test: the two changed skills (schema consistency review)

**Interfaces:**
- Consumes: Plan 1 assignment schema and the existing step index/status contracts.
- Produces: recommendation fields in step index and resolved current-attempt plus append-only assignment history in step status.

- [ ] **Step 1: Write the failing schema assertions**

Define required examples for `model_assignments.implementer`,
`model_assignments.verifier`, recommendation rationale/capabilities, current attempt
assignment, application result, and prior attempt history.

- [ ] **Step 2: Run the missing-field check**

```powershell
rg -n "model_assignments|recommendation|attempt.*assignment|application|history" skills/step-index-format/SKILL.md skills/step-status-format/SKILL.md
```

Expected: FAIL for the new model fields.

- [ ] **Step 3: Update index and context formats**

Add optional decomposer recommendations and required orchestrator-resolved assignments.
State that the original recommendation remains auditable and that documentation models do
not belong in step decomposition.

- [ ] **Step 4: Update status format**

Add the resolved assignment for the current attempt, application result, and append-only
attempt records. Define retry preservation and explicit escalation fields: trigger, prior
model, new model, and authorizing policy rule.

- [ ] **Step 5: Validate cross-file names**

```powershell
rg -n "portable_id|source|rationale|applied|evidence|fallback|attempt|escalation" skills/step-index-format/SKILL.md skills/step-status-format/SKILL.md
```

Expected: PASS with consistent names and no documentation assignment fields in decomposition.

- [ ] **Step 6: Commit**

```bash
git add skills/step-index-format/SKILL.md skills/step-status-format/SKILL.md
git commit -m "docs: persist model assignments in step state"
```

### Task 3: Update the Step Decomposer contract

**Files:**
- Modify: `agents/step-decomposer.agent.md`
- Test: `agents/step-decomposer.agent.md` (role-boundary review)

**Interfaces:**
- Consumes: the updated step formats and catalog/policy contracts.
- Produces: per-step implementer/verifier recommendations, capability requirements, complexity signals, and documentation profile metadata without final documentation assignments.

- [ ] **Step 1: Write the failing role assertions**

Require the agent instructions to say that recommendations are non-final, documentation
model selection is deferred, and the decomposer records required capabilities, complexity,
rationale, and independent-verification recommendations.

- [ ] **Step 2: Run the missing-rule check**

```powershell
rg -n "recommend|documentation.*model|final|capabilit|complexity|independent" agents/step-decomposer.agent.md
```

Expected: FAIL for at least the new routing boundaries.

- [ ] **Step 3: Update the role instructions**

Add the model catalog and routing policy as inputs, require structured recommendations in
step index/context artifacts, prohibit final assignment and application decisions, and
require documentation profile signals for the plan auditor/decomposer handoff.

- [ ] **Step 4: Validate and commit**

```powershell
rg -n "non-final|orchestrator|documentation.*after|required capabilities|rationale|verification" agents/step-decomposer.agent.md
```

Expected: PASS.

```bash
git add agents/step-decomposer.agent.md
git commit -m "docs: define decomposer model recommendations"
```

### Task 4: Update the Implementation Orchestrator contract

**Files:**
- Modify: `agents/implementation-orchestrator.agent.md`
- Test: `agents/implementation-orchestrator.agent.md` (procedure and state review)

**Interfaces:**
- Consumes: all formats and role rules from Tasks 1-3 and Plan 1.
- Produces: an ordered orchestration procedure for configuration confirmation, freezing, preflight, central selection, adapter application, persistence, retries, resume, documentation assignments, and legacy mode.

- [ ] **Step 1: Write the failing procedure assertions**

List the required ordered events: effective configuration confirmation, frozen run copies,
one preflight, role requirement evaluation, portable selection, host resolution, pre-
delegation persistence, application, evidence persistence, retry preservation, and late
documentation assignment.

- [ ] **Step 2: Run the missing-rule check**

```powershell
rg -n "catalog|policy|preflight|model_assignment|resolve|apply|runtime|fallback|escalat|resume|documentation" agents/implementation-orchestrator.agent.md
```

Expected: FAIL or show no complete ordered model-routing procedure.

- [ ] **Step 3: Add central routing ownership**

Extend required skills and rules so the orchestrator validates IDs/capabilities/policy,
selects portable IDs, invokes exactly one adapter preflight, resolves/applies through the
adapter, and persists the assignment before delegation and the application result after it.

- [ ] **Step 4: Add failure, retry, and resume behavior**

Document optional versus required application, explicit ordered fallbacks, adapter failure
handling, immutable prior attempts, policy-authorized escalation, fingerprint mismatch
behavior, and Pi's unapplied warning. Prohibit silent parent-model substitution.

- [ ] **Step 5: Add documentation timing**

Require writer and verifier assignments only after final verification and implementation
evidence. Require independent verifier selection and assignment persistence in the
frontmatter format from Plan 1.

- [ ] **Step 6: Validate and commit**

```powershell
rg -n "before delegation|preflight.*once|requested|resolved|applied|evidence|require_application|retry|escalation|fingerprint|Pi|final verification|documentation" agents/implementation-orchestrator.agent.md
```

Expected: PASS with all ordered decisions represented.

```bash
git add agents/implementation-orchestrator.agent.md
git commit -m "docs: define orchestrator model routing procedure"
```

## Plan Exit Criteria

- Run, step index, context, status, handoff, and documentation formats use compatible field names.
- The decomposer can recommend but cannot finalize; the orchestrator owns final selection.
- Retry and resume rules preserve immutable model evidence.
- Plan 3 can document the finalized host behavior without adding missing orchestration rules.
- `git diff --check` passes for the plan's commits.
