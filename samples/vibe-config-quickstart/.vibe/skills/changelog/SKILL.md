---
name: changelog
description: Drafts a release changelog entry from recent git history using a project template. Use when preparing a release, or when the user mentions a changelog, release notes, or runs /changelog.
---

# Changelog drafter

Turn recent git history into a changelog entry. Steps:

1. Get today's real date: `date +%Y-%m-%d` (do not guess it).
2. Read the recent history: `git log --oneline -n 20`.
3. Group the commits into Added, Changed, Fixed (drop noise like merge commits
   and formatting-only changes).
4. Fill in the template in `assets/template.md` with the date from step 1 and
   the grouped entries.
5. Print the finished entry. Do not write files unless the user asks.

Invoke this skill with `/changelog`, optionally followed by a version number,
for example `/changelog 0.2.0`.

This skill runs `git` and `date`, so use it with an agent that has the `bash`
tool (for example `test-writer`). The read-only `reviewer` agent cannot run it,
which shows how an agent's tool posture gates what a skill can do.
