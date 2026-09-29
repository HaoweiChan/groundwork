---
id: TASK-10
title: >-
  groundwork-retro: one-shot ledger report for agents and an HTML view for
  humans
status: To Do
assignee: []
created_date: '2026-09-29 15:56'
labels:
  - self-improvement
  - retro
dependencies:
  - TASK-2
  - TASK-4
documentation:
  - docs/harness-upgrade.html
priority: medium
ordinal: 10000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
`tasks/pr-loop-ledger.jsonl` and `tasks/reviews/*.json` are written on every run, read by nothing, and hard for people to read. The ratchet (every rule traces to a failure; Osmani) needs evidence of repetition, and these files already hold it. Shape follows ponytail's one-shot report skills: read only, change nothing, end with one summary line.

Change: New skill `plugin/skills/groundwork-retro` with stdlib `scripts/ledger_report.py`. Text mode for agents (<= 60 lines): calls per task, repair rate, not-met rate, gate failures, handoff-size trend, recurring findings grouped by question and top-level path. When a group spans >= 3 distinct tasks, print one ready-to-run `backlog task create --draft -l ratchet` line naming those tasks and proposing the cheapest enforcement (case, then lint, then hook). `--html <path>` writes one self-contained page (data inlined, no network), like graphify's graph.html; the default output path is gitignored. Write GW-021.

Plan: docs/harness-upgrade.html

Probe: none — plugin text/stdlib change with no deployed or live behavior.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 test_ledger_report.py fails first, then passes: a fixture where one finding group spans 3 tasks prints exactly one draft line naming those 3 tasks
- [ ] #2 Below the threshold, no draft line is printed
- [ ] #3 `--html` writes a single file with no external URLs that contains every task id in the fixture
- [ ] #4 Text output is <= 60 lines for a 50-task fixture, and the script writes nothing except the requested --html file
- [ ] #5 Both runtimes register the skill (test_plugin_contracts parity); GW-021 exists with one INDEX.md line
<!-- AC:END -->
