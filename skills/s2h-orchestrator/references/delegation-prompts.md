# Delegation prompt blocks

Verbatim delegation prompt blocks used by `s2h-orchestrator` and its owner-tier
agents. Send exactly the block for the role being delegated, with only placeholder
values substituted and nothing else added. Placeholder definitions live in `SKILL.md`
under "Delegation prompt templates".

**s2h-PlanAuditor**

```text
Role: s2h-PlanAuditor
Task ID and attempt: plan-audit, attempt 1
Paths:
  - Plan: <plan-path>
  - Run directory: <run-dir>
Constraint: read-only for repository files; writes only the audit report,
requirements.json, and documentation context files under <run-dir>
```

**s2h-ImplementationPhaseOwner**

```text
Role: s2h-ImplementationPhaseOwner
Task ID and attempt: step-execution, attempt <n>
Paths and values:
  - Run directory: <run-dir>
  - Chunk index: <run-dir>/chunk-index.json
  - Per-loop retry cap L: <L>
Constraint: owns the step-execution phase; delegates one s2h-StepLoop per
step in dependency order; reports only its bounded summary
```

**s2h-PlanDecomposer**

```text
Role: s2h-PlanDecomposer
Task ID and attempt: decomposition, attempt <n>
Paths and values:
  - Plan: <plan-path>
  - Plan audit: <run-dir>/s2h-plan-audit.json
  - Requirements: <run-dir>/requirements.json (only when the audit ran)
  - Per-loop retry cap L: <L>
Constraint: file-modifying for .agent-work files only, never committed; owns
the decomposition phase end to end and delegates its own loops per
s2h-plan-decomposition
```

**s2h-FinalVerificationOwner**

```text
Role: s2h-FinalVerificationOwner
Task ID and attempt: final-verification, attempt <n>
Paths and values:
  - Plan: <plan-path>
  - Run directory: <run-dir>
  - Per-loop retry cap L: <L>
Constraint: owns the final-verification loop; delegates s2h-FinalVerifier and
re-invokes one s2h-StepLoop per affected step within cap L; reports only its bounded summary
```

**s2h-StepImplementer**

```text
Role: s2h-StepImplementer
Task ID and attempt: <step-id>, attempt <n>
Paths:
  - Step context: <run-dir>/steps/<step-id>.md
  - Latest checkpoint: <run-dir>/checkpoints/<step-id>.json (when one exists)
  - Verifier report (repair rounds only): <verifier-report-path>
Constraint: file-modifying; work only within the step's declared scope; run
required validation and commit before returning; report the commit hash
```

**s2h-StepVerifier**

```text
Role: s2h-StepVerifier
Task ID and attempt: <step-id>, attempt <n>
Paths:
  - Step context: <run-dir>/steps/<step-id>.md
  - Implementer handoff: <implementer-handoff-path>
  - Relevant checkpoint: <run-dir>/checkpoints/<step-id>.json (when one exists)
Constraint: read-only
```

**s2h-FinalVerifier**

```text
Role: s2h-FinalVerifier
Task ID and attempt: final-verification, attempt <n>
Paths and values:
  - Plan: <plan-path>
  - Chunk index: <run-dir>/chunk-index.json
  - Handoff reports: every persisted report under <run-dir>/reports/
  - Commit and repository state: as recorded in <run-dir>/run.json
Constraint: read-only
```

**s2h-DocumentationPhaseOwner**

```text
Role: s2h-DocumentationPhaseOwner
Task ID and attempt: documentation, attempt <n>
Paths and values:
  - Run directory: <run-dir>
  - Final changed files (one bullet per file):
    - <changed-file-path-1>
    - <changed-file-path-2>
  - Source-doc context: <run-dir>/documentation/source-doc-context.md
  - User-doc context: <run-dir>/documentation/user-doc-context.md
  - Per-loop retry cap L: <L>
Constraint: owns the documentation phase; builds source-doc assignments for the
listed changed files, runs one bounded writer-verifier cycle per assignment, creates
and verifies the user-doc assignment last; reports only its bounded summary
```

**s2h-DocumentationWriter, source-doc assignment** (one per changed file)

```text
Role: s2h-DocumentationWriter
Task ID and attempt: source-doc/<changed-file>, attempt <n>
Paths:
  - Documentation context: <run-dir>/documentation/source-doc-context.md
  - Final changed files (one bullet per file):
    - <changed-file-path-1>
    - <changed-file-path-2>
  - Relevant step reports (one bullet per report):
    - <step-report-path-1>
    - <step-report-path-2>
Constraint: file-modifying; edit only the assigned documentation set; make a
separate documentation commit before returning
```

**s2h-DocumentationVerifier**

```text
Role: s2h-DocumentationVerifier
Task ID and attempt: doc-verify/<assignment-id>, attempt <n>
Paths:
  - Assignment brief: the assignment's Markdown context file
  - Written documentation: the documented file path(s)
Constraint: read-only
```

**s2h-DocumentationWriter, user-doc assignment**

```text
Role: s2h-DocumentationWriter
Task ID and attempt: user-doc, attempt <n>
Paths:
  - Documentation context: <run-dir>/documentation/user-doc-context.md
  - Final verified requirements: <run-dir>/requirements.json
Constraint: file-modifying; make a separate documentation commit before returning
```
