---
id: TASK-13
title: Retro writes a sanitized upstream feedback packet for Groundwork
status: To Do
assignee: []
created_date: '2026-09-29 15:56'
labels:
  - self-improvement
  - upstream
dependencies:
  - TASK-12
documentation:
  - docs/harness-upgrade.html
priority: low
ordinal: 13000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Groundwork improves fastest from the repositories that use it. Sending project data out is the human's decision, so the tool prepares the packet and never sends it.

Change: `groundwork-retro --upstream` writes `tasks/groundwork-feedback.md` with only groundwork-class signals: counts, rule ids, GW ids, groundwork_version and the scoreboard. No code, file paths, finding text or task titles. It prints the `gh issue create -R HaoweiChan/groundwork -l feedback --body-file tasks/groundwork-feedback.md` command for the human to run. In the Groundwork repo, a feedback issue becomes a draft labelled `upstream` that a maintainer promotes.

Plan: docs/harness-upgrade.html

Probe: none — plugin text/stdlib change with no deployed or live behavior.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 test_ledger_report.py fails first, then passes: the packet built from a fixture contains none of the fixture's file paths, finding claims or task titles
- [ ] #2 The packet carries the version scoreboard and the groundwork signal counts
- [ ] #3 The script never calls gh or the network; it only prints the command
- [ ] #4 groundwork-retro documents the intake: feedback issue -> `backlog task create --draft -l upstream` in the Groundwork repo
<!-- AC:END -->
