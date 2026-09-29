---
id: TASK-9
title: pr-loop loads per-state detail on demand
status: To Do
assignee: []
created_date: '2026-09-29 15:56'
labels:
  - tokens
  - pr-loop
dependencies:
  - TASK-2
  - TASK-4
documentation:
  - docs/harness-upgrade.html
priority: low
ordinal: 9000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
pr-loop SKILL.md is 16,864 B and loads whole on every run, though the PR body template, JSON schemas, worktree commands and ledger format are each used in one state. Load detail when it is needed (Anthropic context engineering; Osmani).

Change: SKILL.md keeps the state machine, role table, budget, routing table and a short paragraph per state (<= 8,000 B). Detail moves to `references/implement.md`, `references/verify.md` and `references/evidence.md`, each read on entering its state. No rule changes.

Plan: docs/harness-upgrade.html

Probe: none — plugin text/stdlib change with no deployed or live behavior.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A plugin test fails first, then passes: SKILL.md is <= 8,000 bytes and every references/ file it names exists
- [ ] #2 Contract tests that check pr-loop text read the whole skill directory and keep their meaning
- [ ] #3 Codex loads the reference files (checked against the codex-plugin-domain rules)
- [ ] #4 GW-020 lists the size cap under Enforced by
<!-- AC:END -->
