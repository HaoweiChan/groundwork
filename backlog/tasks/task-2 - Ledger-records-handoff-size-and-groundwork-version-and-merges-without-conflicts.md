---
id: TASK-2
title: >-
  Ledger records handoff size and groundwork version, and merges without
  conflicts
status: To Do
assignee: []
created_date: '2026-09-29 15:56'
labels:
  - measure
  - pr-loop
dependencies: []
documentation:
  - docs/harness-upgrade.html
priority: high
ordinal: 2000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Reviewer token counts are null whenever the host hides them, so no later change can be shown to save anything; compression hides interaction cost that success rates miss (Liu 2026). Two open PRs that each append a ledger line conflict at end of file. The ledger stays the tracked machine store; humans read a generated view (see the retro task).

Change: Every `model_routes` entry gets `handoff_bytes` (byte size of the packet handed to that subagent). Every ledger line gets `groundwork_version`, read from `.groundwork-version` (null when absent). The scaffold ships `.gitattributes` with `tasks/pr-loop-ledger.jsonl merge=union`, and groundwork-init seeds it. Write GW-018.

Plan: docs/harness-upgrade.html

Probe: none — plugin text/stdlib change with no deployed or live behavior.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 test_pr_loop_v4.py fails first, then passes: the ledger example has `handoff_bytes` on every model route and a top-level `groundwork_version`
- [ ] #2 pr-loop § Ledger says how `handoff_bytes` is computed and that `groundwork_version` is null without `.groundwork-version`
- [ ] #3 A plugin test merges two branches that each append one ledger line in a temporary repo using the scaffold `.gitattributes`, with no conflict
- [ ] #4 GW-018 exists with the three-line header (tracked JSON is the machine store, humans read a generated view, handoff size is measured) and one INDEX.md line
<!-- AC:END -->
