---
name: s2h-design
description: >-
  Build an implementation-ready design document interactively.
user-invocable: true
disable-model-invocation: true
argument-hint: <request> [existing-draft-path]
---

# Design Process

Produce the design document that `s2h-orchestrator` later consumes as its
immutable `Plan:` input. The task is to make the design, not implement it.
This skill is read-only: investigation uses file reads, searches, history,
and non-mutating shell commands only; the only files this skill may create
or modify are the design document(s) themselves.

## Inputs
- Required: a prompt describing what you want designed - a feature, refactor,
  migration, or new subsystem. If absent, ask for it before doing anything else.
- Optional: an existing draft, plan, or design document to build from. When one
  exists in scope, ask whether this run extends it or produces a new document
  alongside it; never assume either way.
- Deeper level of an existing hierarchy: the immediately-upper design document and your
  chunk within it are the base for this run. If several chunks exist and none is named, ask
  which one to refine before investigating.

## Procedure
1. **Investigate.** Read the relevant code, tests, documentation, and history.
   Use only tools that change nothing - file reads, searches, `git log`,
   `git diff`. Record what exists today as verified facts: behavior, constraints,
   conventions. Label anything inferred as inference.
2. **Restate understanding and ask first.** Before drafting anything, present your
   reading of the request to the user: the goal in their confirmed words, the scope
   you can see, the current-state facts you recorded, where the finished document
   should live (this repo's convention is `docs/<date>-<slug>.md`), and every open
   question. Do not proceed until they confirm or correct it.
3. **Decide by asking.**
   - When a request admits more than one interpretation, ask which one is correct;
     never pick silently.
   - When several near-equal options exist for a design choice, present each with its
     tradeoffs and your recommendation if warranted, then wait for the decision.
   - Ask early and often: after investigation, on every scope question, and on any
     interface or behavior that has more than one viable shape before it is written
     into the draft.
   - Record each confirmed decision verbatim as it arrives; the document states only
     the settled choice, never how it was reached. An unconfirmed position is not a
     decision: until resolved, flag it `OPEN` with the exact question instead of deciding it.
4. **Match detail level to scope.** The closer the design sits to implementation, the
   more low-level it must be:
   - Large scope (system or new subsystem): goals and non-goals, component
     responsibilities, major boundaries, external interfaces at contract level, key
     risks. No function signatures or field lists.
   - Medium scope (module or feature): add data flow per unit, public API contracts,
     error and edge behavior per unit, ordering between units.
   - Narrow scope (file or group of functions): exact file paths, function and data
     shapes, ordered steps, acceptance criteria for each behavior.
   It is always easier to add detail later than remove it: do not force low-level
   detail into a broad design; deepen a section only when the user will implement from it.
   If investigation shows a chunk's content already meets the agreed level - existing code or
   settled prior work - refining it means verifying and recording that, not inventing
   lower-level detail to justify the run. A document whose sections are all confirmed
   decisions or verified facts at its level is complete; nothing more belongs in it.
   A broad-scope document must be divisible by construction: it explicitly names its
   decomposable units, and each unit carries enough content - goal, boundaries, known
   interfaces, open questions - to start a deeper-level design run on its own without
   re-deriving the top level. Top-level documents of large systems commonly need two or
   three such refinements before one reaches narrow-scope detail that can serve as the
   orchestrator's `Plan:` input directly.
5. **Draft and review incrementally.** Present one drafted section (or a small batch)
   at a time, wait for feedback, revise, then move on. The document is updated as
   decisions accumulate so its sections never drift apart. Every claim must trace to
   a confirmed decision or a verified fact; unresolved questions stay flagged `OPEN`
   instead of being decided silently.
6. **Finalize.** When every section is approved, delegate the consistency pass to a fresh
   subagent: hand it only the finished document - plus its immediate upper-level document when
   this was a deeper-level run - and the defect classes defined by `s2h-plan-audit`. Its context
   contains no drafting conversation, so its review is unbiased by how the document was written.
   Tell it that OPEN-flagged items are explicit user deferrals recorded under Open Items, not
   defects; it reports findings only and does not fix or redesign anything. Fix what it finds
   before declaring done, returning to the user any finding whose resolution is a decision. Every
   requirement must have an observable outcome a command, test, or inspection can verify.
   Report the final file path and whether it can serve directly as workflow input. If it reached
   a sufficiently narrow scope, it is the immutable `Plan:` input for `s2h-orchestrator` or
   `s2h-plan-audit`; if it stopped at large or medium scope, list its decomposable units and
   which still need deeper-level runs before one document in the tree is ready as workflow input.

## Working across tiers

A tiered design is a tree of documents - broad at the root, narrowing toward leaves that
are detailed enough to feed the orchestrator directly.

- **Starting deeper from a chunk.** Base this run on your parent document and its
  description of the chunk; treat settled decisions there as given. Do not re-litigate them
  while refining the chunk - unless deeper work touches an upper level (see the next point).
- **When deep-level work touches an upper level.** It can happen two ways: a deeper finding
  contradicts or invalidates part of an upper-level document, or it reveals a better design that
  requires revisiting a settled choice. Never dismiss the new direction just because it conflicts
  with a settled decision - and never adopt it silently either. In both cases stop drafting and
  present to the user what is being proposed, why it merits attention, and its scope of impact:
  which sections are affected, how much rework that implies, and whether already-completed
  sibling documents may now be stale. Wait for direction before updating the affected documents;
  never patch higher levels silently mid-run.

## Document contents
Every design document follows this section structure, in order, at its agreed scope level:

1. **Goal** - in the user's confirmed words.
2. **Scope and non-goals** - what is explicitly out of scope.
3. **Tier** (omit for root documents) - path of the parent document and which chunk this
   document refines.
4. **Units** (include when the scope decomposes into chunks) - each chunk's name, a description
   sufficient to carry forward whatever follows from it alone; mark as **refined** or **to be
   refined**, unmarked meaning no refinement is necessary. All-or-nothing applies per document:
   either every chunk is refined by a child document or none are - since only leaves feed the
   implementation, unrefined chunks in a mixed document would never be implemented.
5. **Current state** - verified facts about what exists today.
6. **Decisions** - each question asked, the options considered, and the choice made.
7. **Design** - architecture and behavior at the agreed detail level.
8. **Acceptance criteria** - observable, verifiable outcomes for every requirement.
9. **Open items** - questions the user explicitly deferred, each with what it blocks.

## Boundaries
- Writes: only the design document(s). No code edits, config changes, branches,
  commits, or other artifacts; nothing else in the repository may change while this
  skill runs.
