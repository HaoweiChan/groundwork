---
id: TASK-5
title: Pre-commit blocks a baseline move without an ADR
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
ordinal: 5000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
docs/groundwork.md says the baseline moves only by an explicit decision recorded in an ADR; nothing enforces it. A git hook enforces it for both Claude Code and Codex.

Change: The scaffold `.githooks/pre-commit` exits 1 when `.eval-baseline.json` is staged and no file under `specs/decisions/` is staged with it, and the message names the rule. The check runs before the eval-harness early exit.

Plan: docs/harness-upgrade.html

Probe: none — plugin text/stdlib change with no deployed or live behavior.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A plugin test fails first, then passes: in a temporary repo, staging only `.eval-baseline.json` makes the scaffold pre-commit exit 1
- [ ] #2 Staging `.eval-baseline.json` together with a new `specs/decisions/ADR-*.md` passes that check
- [ ] #3 Commits that do not touch the baseline behave as before
- [ ] #4 GW-019 lists the hook under Enforced by
<!-- AC:END -->
