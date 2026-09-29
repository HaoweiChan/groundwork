---
id: TASK-11
title: Ratchet drafts enter the loop and humans promote them
status: To Do
assignee: []
created_date: '2026-09-29 15:56'
labels:
  - self-improvement
  - pr-loop
dependencies:
  - TASK-10
documentation:
  - docs/harness-upgrade.html
priority: low
ordinal: 11000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Improve contexts with small appended updates plus curation, never wholesale rewrites, which cause context collapse (ACE, ICLR 2026). Unreliable feedback and irreversible changes are the main risks of self-evolving agents (Zhou et al. survey, 2026).

Change: `/pr-loop next` runs groundwork-retro first and files any suggested ratchet as a draft; it never implements one. The debt rule accepts `tasks <ids>` as evidence. A promoted ratchet's acceptance is a case, lint or hook that goes red on the recorded repros. Retro output never leads a model to edit CLAUDE.md, a skill or a hook directly.

Plan: docs/harness-upgrade.html

Probe: none — plugin text/stdlib change with no deployed or live behavior.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 test_pr_loop_v4.py fails first, then passes: pr-loop names the retro step at `next` and files ratchets with --draft only
- [ ] #2 The debt rule accepts a `tasks <ids>` reference alongside `case <id>` and `run <id>`
- [ ] #3 pr-loop states that a ratchet task's acceptance must go red on its recorded repros
- [ ] #4 GW-021 records that instruction files are never edited directly from retro output
<!-- AC:END -->
