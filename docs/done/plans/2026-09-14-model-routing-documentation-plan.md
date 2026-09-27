# Model Routing Documentation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the separately invocable model-configuration workflow and document dynamic routing behavior for Copilot, oh-my-pi, and Pi users.

**Architecture:** The configuration skill guides users through repository catalog and policy edits, validates them before writing, preserves unrelated fields, and requires confirmation. The README explains the portable routing model, run-time evidence, host limitations, and installation/configuration boundaries without claiming executable routing exists in this documentation-first phase.

**Tech Stack:** Markdown skill and agent documentation, YAML examples, existing package/plugin discovery, PowerShell and Git checks.

**Spec:** [2026-09-14-dynamic-model-selection-design.md](../specs/2026-09-14-dynamic-model-selection-design.md)

**Prerequisites:** Complete [Model Routing Contracts Implementation Plan](2026-09-14-model-routing-contracts-plan.md) and [Model Routing Orchestration Implementation Plan](2026-09-14-model-routing-orchestration-plan.md).

## Global Constraints

- This phase documents contracts and guided configuration; executable resolver and adapter code is out of scope.
- Repository catalog/policy files stay outside `.agent-work/`; only effective run copies belong under `.agent-work/<run-id>/`.
- Invocation overrides require complete effective-configuration display and explicit confirmation.
- Configuration is structured YAML; model IDs are never interpreted as executable commands.
- Copilot and oh-my-pi have separate adapter responsibilities; Pi model selection is unsupported.
- Documentation must not imply that a resolved model was applied without evidence.

---

### Task 1: Create the guided model-configuration skill

**Files:**
- Create: `skills/model-configuration/SKILL.md`
- Test: `skills/model-configuration/SKILL.md` (workflow and validation review)

**Interfaces:**
- Consumes: `model-catalog-format` and `model-routing-adapter` contracts from Plan 1.
- Produces: a separately invocable guided workflow for creating/editing `.implementation-agent/model-catalog.yaml` and `.implementation-agent/model-policy.yaml`.

- [ ] **Step 1: Write the failing workflow assertions**

Require the skill to cover capability/tier/cost/context/tool questions, host mappings,
role requirements, fallback chains, retry/escalation policy, field-level merge behavior,
pre-write validation, preservation of unrelated fields, confirmation, and prohibition on
writing effective run config under `.agent-work/`.

- [ ] **Step 2: Run the missing-file check**

```powershell
rg -n "capabilit|fallback|retry|confirmation|agent-work|model-catalog|model-policy" skills/model-configuration/SKILL.md
```

Expected: FAIL because the skill does not exist.

- [ ] **Step 3: Write the guided workflow**

Define the invocation inputs, inspection of existing YAML, structured questions, merge
rules, validation sequence, complete effective-configuration display, explicit confirmation,
write behavior, and failure output. Include valid YAML examples for one catalog entry and
one policy role, while keeping host mappings data-only.

- [ ] **Step 4: Validate and commit**

```powershell
rg -n "model-catalog.yaml|model-policy.yaml|field-level|context_window|tools|hosts|fallback|allow_escalation|validate|preserve|confirm|\.agent-work" skills/model-configuration/SKILL.md
```

Expected: PASS.

```bash
git add skills/model-configuration/SKILL.md
git commit -m "docs: add guided model configuration skill"
```

### Task 2: Document host behavior and current implementation status

**Files:**
- Modify: `README.md`
- Test: `README.md` (link, example, and limitation review)

**Interfaces:**
- Consumes: finalized role/orchestrator rules from Plan 2 and adapter behavior from Plan 1.
- Produces: user-facing guidance for configuration locations, override confirmation, frozen run inputs, application evidence, Copilot/oh-my-pi behavior, Pi limitations, and documentation-only phase status.

- [ ] **Step 1: Write the failing documentation assertions**

Require README sections or paragraphs covering model catalog/policy paths, portable IDs,
`require_application`, run copies, evidence levels, fallback warnings, Copilot generated
profiles, oh-my-pi overrides/roles, Pi unsupported status, and the distinction between this
phase's contracts and later executable integration.

- [ ] **Step 2: Run the missing-topic check**

```powershell
rg -n "model catalog|model policy|portable|require_application|agent-work|evidence|Copilot|oh-my-pi|Pi|unsupported" README.md
```

Expected: FAIL or show incomplete coverage.

- [ ] **Step 3: Add concise user documentation**

Add a configuration section with paths and YAML examples, a runtime behavior section with
the honest-application rule and warning outcomes, a host support section distinguishing
Copilot and oh-my-pi from Pi, and a scope note that executable routing follows this
contract/documentation phase. Link to the three relevant skills and the design spec using
repository-relative Markdown links.

- [ ] **Step 4: Validate links and content**

```powershell
rg -n "skills/model-configuration/SKILL.md|skills/model-catalog-format/SKILL.md|skills/model-routing-adapter/SKILL.md|\.implementation-agent/model-catalog.yaml|\.implementation-agent/model-policy.yaml|Pi.*unsupported" README.md
```

Expected: PASS.

```powershell
git diff --check
```

Expected: no output and exit code 0.

- [ ] **Step 5: Commit**

```bash
git add README.md
git commit -m "docs: explain dynamic model selection behavior"
```

### Task 3: Run documentation-first integration review

**Files:**
- Review: `agents/implementation-orchestrator.agent.md`
- Review: `agents/step-decomposer.agent.md`
- Review: `skills/agent-handoff/SKILL.md`
- Review: `skills/documentation-assignment-format/SKILL.md`
- Review: `skills/model-catalog-format/SKILL.md`
- Review: `skills/model-configuration/SKILL.md`
- Review: `skills/model-routing-adapter/SKILL.md`
- Review: `skills/run-ledger-format/SKILL.md`
- Review: `skills/step-index-format/SKILL.md`
- Review: `skills/step-context-format/SKILL.md`
- Review: `skills/step-status-format/SKILL.md`
- Review: `README.md`
- Test: repository-wide documentation consistency checks

**Interfaces:**
- Consumes: all outputs from Plans 1 and 2 plus this plan's configuration and README changes.
- Produces: a review result confirming that every design requirement has an owner and no document claims executable behavior that does not exist.

- [ ] **Step 1: Build the cross-reference assertions**

Check that each shared field has one spelling across the files: `portable_id`, `requested`,
`resolved`, `fallback`, `applied`, `adapter`, `evidence`, `runtime_model`, `warning`,
`preflight`, and `model_assignments`.

- [ ] **Step 2: Run the consistency checks**

```powershell
rg -n "portable_id|requested:|resolved:|fallback:|applied:|adapter:|evidence:|runtime_model:|warning:|preflight:|model_assignments:" agents skills README.md
```

Expected: all terms appear in the owning contracts and no alternate spelling is introduced.

```powershell
rg -n "Pi.*(supported|dynamic|applied)|applied.*true|runtime_model.*selected" README.md agents skills
```

Expected: any Pi mention states unsupported/unapplied, and no documentation claims runtime
application without the evidence rules.

- [ ] **Step 3: Perform the requirement trace review**

Map the design's goals, non-goals, ownership, persistence, adapter, failure, compatibility,
and acceptance sections to the plan tasks. Record any uncovered requirement as a blocking
finding; do not silently mark it complete from file presence.

- [ ] **Step 4: Run final repository checks**

```powershell
git diff --check
```

Expected: no output and exit code 0.

```powershell
Get-ChildItem skills/model-configuration, skills/model-catalog-format, skills/model-routing-adapter | Select-Object FullName
```

Expected: all three skill files exist.

- [ ] **Step 5: Commit the review evidence if the repository convention requires it**

If the review produces only verifier output, leave source files unchanged. If it requires a
factual documentation correction, make that smallest correction, rerun all checks, and
commit it separately:

```bash
git add README.md agents skills
git commit -m "docs: reconcile model routing documentation"
```

## Plan Exit Criteria

- Users can find and configure the catalog/policy without confusing repository config with run state.
- Host-specific behavior and evidence limits are documented accurately.
- Pi is explicitly unsupported and unapplied.
- All design requirements have a traceable documentation owner.
- The repository is ready for a later executable resolver/adapter phase without changing the public contracts.
