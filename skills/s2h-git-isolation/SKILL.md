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

File-modifying subagents validate, commit, and report per
`s2h-atomic-step-commit`. Verification agents are read-only.

Never reset or discard unrelated changes. Never commit `.agent-work/`.
