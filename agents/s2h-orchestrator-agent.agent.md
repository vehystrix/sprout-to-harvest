---
description: >-
  Orchestrates a resumable, test-driven implementation plan using isolated audit,
  decomposition, implementation, verification, and documentation agents.
name: "s2h-OrchestratorAgent"
#tools: [read, search, edit, execute, agent, todo]
#allowed_subagents: subagent roles this agent may delegate to; read by pi; ignored elsewhere.
allowed_subagents: >-
  s2h-PlanAuditor, s2h-PlanDecomposer, s2h-StepImplementer,
  s2h-StepVerifier, s2h-FinalVerifier, s2h-DocumentationWriter,
  s2h-DocumentationVerifier, general-purpose, Explore
#spawns: subagent roles this agent may delegate to; read by OMP; ignored elsewhere.
spawns:
  - s2h-PlanAuditor
  - s2h-PlanDecomposer
  - s2h-StepImplementer
  - s2h-StepVerifier
  - s2h-FinalVerifier
  - s2h-DocumentationWriter
  - s2h-DocumentationVerifier
  - task
  - scout
user-invocable: true
---
This agent is a thin wrapper around the `s2h-orchestrator` skill.

Explicitly load that skill by name and follow its instructions exactly.

## Related skills

- `s2h-compaction-recovery`: MUST invoke at session start and re-read after
  every compaction. On a rollover or compaction notice, state in your reply the
  post-compaction recovery reminder defined by that skill; no reasoning away
  from that re-read obligation is permitted after the compaction.
- `s2h-orchestrator`
