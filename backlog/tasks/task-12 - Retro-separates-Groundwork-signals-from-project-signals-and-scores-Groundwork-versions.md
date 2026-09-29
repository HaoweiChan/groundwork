---
id: TASK-12
title: >-
  Retro separates Groundwork signals from project signals and scores Groundwork
  versions
status: To Do
assignee: []
created_date: '2026-09-29 15:56'
labels:
  - self-improvement
  - retro
  - upstream
dependencies:
  - TASK-10
documentation:
  - docs/harness-upgrade.html
priority: low
ordinal: 12000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The same ledger can improve Groundwork itself. Some signals are about the project's code (findings on its paths); others are about the loop (a rejected verifier output, a task ending not met after call 2, a failed or substituted model route, repeated preflight bounces, handoff size over budget). With `groundwork_version` on every line, a Groundwork change can be judged on real tasks, as Skill Issue (2026) does by replaying merged PRs. Honesty boundary, as in ponytail-gain: measured numbers only, null stays null, no verdict for a version with fewer than 5 tasks.

Change: Retro classifies each signal as `project` or `groundwork` by fixed rules listed in the skill, and prints a per-version scoreboard: tasks, calls per task, repair rate, not-met rate, median handoff bytes. Write GW-022.

Plan: docs/harness-upgrade.html

Probe: none — plugin text/stdlib change with no deployed or live behavior.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 test_ledger_report.py fails first, then passes: a fixture with a rejected review output and a not-met task reports both as groundwork signals
- [ ] #2 Findings on project paths are reported as project signals only
- [ ] #3 The scoreboard groups by groundwork_version, prints n per version, and prints `insufficient data` below 5 tasks
- [ ] #4 Missing token counts show as unknown and are never estimated
- [ ] #5 GW-022 exists with its header and one INDEX.md line
<!-- AC:END -->
