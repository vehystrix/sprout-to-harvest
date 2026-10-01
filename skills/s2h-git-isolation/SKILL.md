---
name: s2h-git-isolation
description: Only use when explicitly invoked
# description: >-
#   Use when implementing a plan in a Git workspace where clean changes,
#   branch isolation, commit traceability, and preservation of untracked
#   files are required.
user-invocable: false
disable-model-invocation: true
---
# Git-Isolated Implementation

Before a run:

1. Detect whether the workspace is a Git repository.
2. If tracked changes exist, stop and report that the worktree must be clean.
3. Preserve all untracked files.
4. Create and record a new implementation branch from the current commit.

If Git is unavailable, skip branch and commit operations, record `N/A`
for the repository branch and commit fields, and preserve the same
changed-file and validation evidence requirements.

File-modifying subagents validate their step, commit the completed
work, and report the commit hash before returning.
Verification agents are read-only.
When a subagent needs multiple commits for experimentation or rollback,
use a temporary child branch and merge it into the implementation
branch after verification.

Never reset or discard unrelated changes. Never commit `.agent-work/`.
