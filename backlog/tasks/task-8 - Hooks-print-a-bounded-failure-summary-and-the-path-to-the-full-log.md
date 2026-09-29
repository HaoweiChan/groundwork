---
id: TASK-8
title: Hooks print a bounded failure summary and the path to the full log
status: To Do
assignee: []
created_date: '2026-09-29 15:56'
labels:
  - tokens
  - hooks
dependencies: []
documentation:
  - docs/harness-upgrade.html
priority: medium
ordinal: 8000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
A hook failure pastes the full unittest or eval log into the agent's context. Success should stay silent and failures should be short but complete enough to act on (Osmani); keep a pointer to the full output, because dropped state gets re-fetched at a cost (Liu 2026).

Change: The source `.claude/hooks/post-edit-invariant.sh`, the scaffold hook and the pre-commit gates print the failing test ids with their first assertion line, at most 40 lines, plus the path of the full log they wrote. Success stays silent.

Plan: docs/harness-upgrade.html

Probe: none — plugin text/stdlib change with no deployed or live behavior.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A plugin test fails first, then passes: the hook run against a fixture with one failing test prints <= 40 lines, names the failing test, and prints a log path that exists
- [ ] #2 A passing run prints nothing and exits 0
- [ ] #3 The scaffold hook meets the same two checks
<!-- AC:END -->
