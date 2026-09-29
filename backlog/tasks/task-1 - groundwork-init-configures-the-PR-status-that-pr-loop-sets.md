---
id: TASK-1
title: groundwork-init configures the PR status that pr-loop sets
status: To Do
assignee: []
created_date: '2026-09-29 15:56'
labels:
  - bug
  - init
dependencies: []
documentation:
  - docs/harness-upgrade.html
priority: high
ordinal: 1000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
pr-loop § EVIDENCE runs `backlog task edit <id> -s PR`, but groundwork-init step 2 runs `backlog init --defaults`, which configures only To Do, In Progress and Done. Reproduced with Backlog.md 1.53.0 on a fresh repo: `Invalid status: PR. Valid statuses are: To Do, In Progress, Done`. Every newly initialized repo fails at the loop's last step.

Change: groundwork-init adds `PR` between In Progress and Done in `backlog/config.yml` statuses, additively: an existing custom list keeps its entries and gains `PR` once.

Plan: docs/harness-upgrade.html

Probe: none — plugin text/stdlib change with no deployed or live behavior.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A plugin contract test fails first, then passes: groundwork-init's task-store step adds the `PR` status to `backlog/config.yml`
- [ ] #2 The step is additive: existing statuses are kept and `PR` is added once
- [ ] #3 pr-loop and groundwork-init name the same status string
<!-- AC:END -->
