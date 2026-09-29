---
id: TASK-6
title: Agents cannot bypass hooks with --no-verify or force-push
status: To Do
assignee: []
created_date: '2026-09-29 15:56'
labels:
  - guardrail
  - hooks
dependencies: []
documentation:
  - docs/harness-upgrade.html
priority: medium
ordinal: 6000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
A hook cannot stop `git commit --no-verify` from skipping it. Only 12 of 391 repos have any deny rules (Marmelab 2026). Decision 2026-09-29: an emergency bypass is a human-only action. Claude Code's prefix-based Bash deny rules miss reordered arguments (`git commit -m x --no-verify`), so the block is a PreToolUse hook.

Change: A PreToolUse hook on Bash exits 2 for `git commit` with `--no-verify`/`-n` and for `git push` with `--force`/`-f`/`--force-with-lease`, in this repo and in the scaffold (groundwork-init registers it with the other hooks). Hard rule 5 in CLAUDE.md/AGENTS.md says the bypass is the human's call. GW-019 records the Codex parity gap.

Plan: docs/harness-upgrade.html

Probe: none — plugin text/stdlib change with no deployed or live behavior.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A plugin test fails first, then passes: the hook exits 2 for `git commit --no-verify -m x`, `git commit -m x --no-verify`, `git commit -n -m x`, `git push --force` and `git push -f origin main`
- [ ] #2 The hook exits 0 for a normal `git commit -m x` and a plain `git push`
- [ ] #3 This repo's `.claude/settings.json` and the scaffold settings register the hook
- [ ] #4 Hard rule 5 states that only a human may bypass hooks; GW-019 names the Codex parity gap
<!-- AC:END -->
