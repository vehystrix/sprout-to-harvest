# Delegation prompt blocks

Verbatim delegation prompt blocks for `s2h-orchestrator`. Send exactly the block
for the role being delegated, with only placeholder values substituted and nothing
else added. Placeholder definitions live in `SKILL.md` under "Delegation prompt
templates".

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

**Documentation context format check** (one delegation per file)

```text
Role: read-only documentation-context format checker
Task ID and attempt: doc-format-check/<file-name>, attempt 1
Paths:
  - Documentation context file: <doc-context-file>
Skills: s2h-doc-context-format, s2h-handoff
Instructions: Read exactly the named documentation context file. Apply every
s2h-doc-context-format validation rule that a single file can satisfy. Do not
check any other file and do not edit anything. Save your complete handoff per
s2h-handoff, then return only a summary naming status and its path: VERIFIED if the
file fully conforms, INCOMPLETE with details.findings naming each defect, BLOCKED if
the file is missing or unreadable.
Constraint: read-only
```

**Step context format check** (one delegation per step file)

```text
Role: read-only step-context format checker
Task ID and attempt: step-format-check/<step-id>, attempt 1
Paths:
  - Step file: <run-dir>/steps/<step-id>.md
Skills: s2h-step-context-format, s2h-handoff
Instructions: Read exactly the named step file. Apply every
s2h-step-context-format validation rule that a single file can satisfy. Do not
check any other file and do not edit anything. Save your complete handoff per
s2h-handoff, then return only a summary naming status and its path: VERIFIED if the
file fully conforms, INCOMPLETE with details.findings naming each defect, BLOCKED if
the file is missing or unreadable.
Constraint: read-only
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
