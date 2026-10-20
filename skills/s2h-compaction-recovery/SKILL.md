---
name: s2h-compaction-recovery
description: "MUST invoke at session start and whenever context may be incomplete or compacted"
user-invocable: false
disable-model-invocation: false
---

# Compaction Recovery

The filesystem survival list is authoritative. Conversation text, compacted
summaries, remembered instructions, and pre-compaction reminders are not
authoritative substitutes for it.

## No waiver after compaction

Recovery does not carry across compactions. Having written your survival list
and saved state before a compaction is NOT satisfying this protocol; after
every compaction you MUST re-read this skill and run the full recovery
protocol from step 1. Reasoning that the core actions are already done, or
that a re-read would only repeat information you have acted on, is a
violation of this mandate. The rollover notice itself (save state and
continue) is not the recovery path; it is the trigger to run it.

## Recovery triggers

Run the recovery protocol whenever any of the following holds:

- A compaction, rollover, summarization, truncation, or context-reset marker
  is visible;
- The session resumes after an interruption;
- Expected prior context is missing or appears summarized;
- Persisted task state refers to a governing skill whose authoritative text
  has not been read during the current context;
- You cannot confidently determine whether all session-scoped skills remain
  available in full.

Do not require proof that compaction occurred; uncertainty is sufficient.
Running recovery unnecessarily is safe, and recovery MUST be idempotent.

If advance notice of a compaction is available, state this reminder verbatim
in your reply:

> After this compaction I WILL reload the `s2h-compaction-recovery` skill
> and MUST run its recovery protocol.

## Session-start protocol

1. Determine the current run, role, task, and session identifiers from
   persisted workflow state. Generate a session identifier only if no stable
   one already exists; if you generate one, record it in both the survival
   list and the main run or task state.
2. Compute the session-scoped governing skill set: skills explicitly loaded
   or required for the current role and task. Do not include operation-
   scoped reference material needed only by a single immediate action.
3. Write the complete survival list atomically using the format below.
4. Update the same list whenever a skill becomes, or ceases to be,
   session-scoped.

## Recovery protocol

1. Locate the current survival list with the discovery rules below.
2. Confirm that the list names the current session, role, and task against
   persisted state; do not merge unrelated or stale lists.
3. Read the complete survival list.
4. Canonicalize and deduplicate skill paths within this recovery run.
5. Read this recovery skill first, then read every other listed skill exactly
   once during this run. Never treat remembered, quoted, visible, or
   summarized skill text as a substitute for reading its authoritative file.
6. If a required skill cannot be located or read, do not silently omit it.
   Stop the governed workflow and report: the skill name, its recorded path,
   the survival-list path, and the locations searched.
7. Before making further consequential changes, record an internal checklist
   or persisted recovery record naming: the survival list used, every skill
   successfully re-read, and any recovery errors.
8. At the next normal workflow checkpoint, validate observable artifacts
   against the authoritative re-read skill text, not compaction summary
   residue.

## Survival-list discovery

Check these locations in order:

1. The survival-list path recorded in current persisted run or task state.
2. In an active `s2h` run: `<run-dir>/sessions/<role>-<session-id>-survivable.md`.
3. Otherwise: `<cwd>/.s2h-survivable/<role>-<session-id>.md`.

Search parent directories only as required to locate established project or
run state. Do not union every survival list found in a directory. Host-
provided durable session memory MAY store the survival-list path and session
ID as an additional discovery hint, but it is not the canonical survival list.

## Survival-list format

The list is a short Markdown file. Exact formatting is not load-bearing; what
matters is each skill's path and why it governs the session. Keep this shape:

```
# Survival list s2h-survival/v1
session_id: <stable-session-id>
role: <role>
task_id: <task-id, or none>
run_dir: <run-directory, or none>

Skills to re-read after compaction:

- `skills/s2h-tdd/SKILL.md` - required by s2h-step-implementer
```

Use canonical repository-relative paths where possible. Write the complete
current list by atomic replacement; never append entries. Preserve the same
file path and session ID for the lifetime of the session. If no durable
location is writable, state that compaction-safe recovery cannot be
guaranteed and continue with the best available non-durable mechanism.
