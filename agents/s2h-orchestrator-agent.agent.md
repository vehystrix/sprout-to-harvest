---
description: >-
  Orchestrates a resumable, test-driven implementation plan using isolated audit,
  decomposition, implementation, verification, and documentation agents.
name: "s2h-OrchestratorAgent"
#tools: [read, search, edit, execute, agent, todo]
spawns:
  - s2h-PlanAuditor
  - s2h-PlanDecomposer
  - s2h-StepImplementer
  - s2h-StepVerifier
  - s2h-FinalVerifier
  - s2h-DocumentationWriter
  - s2h-DocumentationVerifier
user-invocable: true
---
This agent is a thin wrapper around the `s2h-orchestrator` skill.

Explicitly load that skill by name and follow its instructions exactly.

## Related skills

- `s2h-orchestrator`
