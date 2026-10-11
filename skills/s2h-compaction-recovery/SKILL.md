---
name: s2h-compaction-recovery
description: "MUST invoke at session start and re-read after every context compaction"
user-invocable: false
disable-model-invocation: false
---

# Compaction Recovery

You invoke this skill at session start to write your survival list while you
still know which skills govern the session; you re-read it after every
compaction to run the recovery protocol. If its full text is not visible in
your current context, read `skills/s2h-compaction-recovery/SKILL.md` before
anything else.

## Recovery protocol

1. **Confirm the boundary.** A compaction summary or marker must be visible
   in your transcript. If you cannot confirm one, stop; checkpoint conditional
   reloads cover what this skill misses.
2. **Compute the session skill set** as a union:
   - Every existing survival list in known locations (see 'Placement tiers' below)
   - A description cross-check - for each visible skill description carrying
     an obligation (MUST/REQUIRED), include it if its trigger condition currently
     holds.
   If your own list does not exist yet, write it now from this result so
   later compactions recover deterministically; see 'Writing' below.
3. **Dedupe and read once.** Union all listed skill paths; drop any skill whose
   full text is already visible in context; read each remaining file exactly
   once. Never read a skill twice from different sources.
4. **Verify at the next checkpoint.** Validate observable outputs against the
   re-read text - named fields, enumerated headings - not summary residue.

## Writing your survival list

At session start, write it now while you still know the session's governing
skills; after a compaction, write it in step 2 if no own list exists yet.
Update it mid-session whenever a new skill becomes session-scoped. List only
the entire session; operation-scoped lookup knowledge (one API call shape,
one subtask) does not belong in it.

### Placement tiers:

- Run dir in `s2h` scope: `<run-dir>/sessions/<role>-<id>-survivable.md`, with a header
  naming your role and task id.
- Else host session memory if available.
- Else `<cwd>/.s2h-survivable/<role>-<id>.md`.

`<id>` is a unique token you generate.
