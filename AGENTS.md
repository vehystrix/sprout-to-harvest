# AGENTS.md

## Layout

- `agents/*.agent.md` - 11 role definitions; the orchestrator is a thin wrapper.
- `skills/<name>/SKILL.md` - feature contract directories; every entry MUST
  contain a SKILL.md. Manifests reference `skills/` as a discovery directory,
  so removing an item auto-excludes it (no manifest edit needed).
- `templates/` - model routing/catalog policy JSON templates. NOT skills:
  infrastructure artifacts copied into target repos; no SKILL.md there means
  it is not a valid skill.
- `package.json`, `plugin.json` - manifests referencing `skills/`.

Eight user-facing entry points; the rest set `user-invocable: false`. See the
README Layout section for the list.

## Core Architecture

Two-layer contract:
- A skill defines base capabilities plus a complexity note.
- An agent augments with structured model_recommendations (rationale,
  independent verification recommendation, guardrails).
- Capabilities/complexity live ONLY in the skill; catalog-driven
  recommendations exist ONLY in the agent. An agent NEVER redefines parallel
  content.

## Style & Conformance

- RFC 2119 keywords (MUST, SHALL) in agent/skill files.
- Line length target < 100 chars; up to ~8 over is acceptable (target, not a
  hard limit).
- ASCII-only: no curly quotes, no em/en dashes.
