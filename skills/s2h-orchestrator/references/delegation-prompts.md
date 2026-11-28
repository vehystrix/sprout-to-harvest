# Delegation prompt blocks

Verbatim delegation prompt blocks for the orchestrator's direct delegations.
Send exactly the block for the role being delegated, with only placeholder
values substituted and nothing else added; leaf-role blocks live in each
delegating tier's own skill. Placeholder definitions live in `SKILL.md` under
"Delegation prompt templates".

**s2h-PlanAuditor**

```text
Role: s2h-PlanAuditor
Task ID and attempt: plan-audit, attempt 1
Paths:
  - Plan: <plan-path>
  - Run directory: <run-dir>
Constraint:
  - read-only for repository files
  - write only the audit report, requirements.json, and documentation
    context files under <run-dir>
```

**s2h-ImplementationPhase**

```text
Role: s2h-ImplementationPhase
Task ID and attempt: implementation, attempt <n>
Paths and values:
  - Run directory: <run-dir>
  - Chunk index: <run-dir>/chunk-index.json
  - Per-loop retry cap L: <L>
Duties:
  - delegate one s2h-StepLoop per step in dependency order
Constraint:
  - MUST NOT write or modify repository files, run verification, tests, or repairs;
    delegate that work to subagents
  - report only your bounded summary
  - BLOCKED is a valid terminal outcome: once cap L is consumed or a blocker is
    recorded, stop and report it with its exact resume action; do not spend further
    attempts reaching DONE
```

**s2h-PlanDecomposer**

```text
Role: s2h-PlanDecomposer
Task ID and attempt: decomposition, attempt <n>
Paths and values:
  - Run directory: <run-dir>
  - Plan: <plan-path>
  - Plan audit: <run-dir>/s2h-plan-audit.json
  - Requirements: <run-dir>/requirements.json (only when the audit ran)
  - Per-loop retry cap L: <L>
Duties:
  - delegate your own decomposition loops per s2h-plan-decomposition
Constraint:
  - file-modifying for .agent-work files only; never commit them
  - MUST NOT write or modify repository files, run verification, tests, or repairs;
    delegate that work to subagents
  - BLOCKED is a valid terminal outcome: once cap L is consumed or a blocker is
    recorded, stop and report it with its exact resume action; do not spend further
    attempts reaching DONE
```

**s2h-FinalVerificationPhase**

```text
Role: s2h-FinalVerificationPhase
Task ID and attempt: final-verification, attempt <n>
Paths and values:
  - Plan: <plan-path>
  - Run directory: <run-dir>
  - Per-loop retry cap L: <L>
Duties:
  - delegate the final verifier, and re-invoke one s2h-StepLoop per affected step within cap L
Constraint:
  - MUST NOT write or modify repository files, run verification, tests, or repairs;
    delegate that work to subagents
  - report only your bounded summary
  - BLOCKED is a valid terminal outcome: once cap L is consumed or a blocker is
    recorded, stop and report it with its exact resume action; do not spend further
    attempts reaching DONE
```

**s2h-DocumentationPhase**

```text
Role: s2h-DocumentationPhase
Task ID and attempt: documentation, attempt <n>
Paths and values:
  - Run directory: <run-dir>
  - Final changed files (one bullet per file):
    - <changed-file-path-1>
    - <changed-file-path-2>
  - Source-doc context: <run-dir>/documentation/source-doc-context.md
  - User-doc context: <run-dir>/documentation/user-doc-context.md
  - Per-loop retry cap L: <L>
Duties:
  - build source-doc assignments for the listed changed files
  - run one bounded writer-verifier cycle per source-doc assignment
  - create and verify the user-doc assignment last
Constraint:
  - MUST NOT write or modify repository files, run verification, tests, or repairs;
    delegate that work to subagents
  - report only your bounded summary
  - BLOCKED is a valid terminal outcome: once cap L is consumed or a blocker is
    recorded, stop and report it with its exact resume action; do not spend further
    attempts reaching DONE
```
