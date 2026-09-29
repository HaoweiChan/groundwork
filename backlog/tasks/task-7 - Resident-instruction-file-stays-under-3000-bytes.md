---
id: TASK-7
title: 'Resident instruction file stays under 3,000 bytes'
status: To Do
assignee: []
created_date: '2026-09-29 15:56'
labels:
  - tokens
  - docs
dependencies:
  - TASK-6
documentation:
  - docs/harness-upgrade.html
priority: medium
ordinal: 7000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
CLAUDE.md and AGENTS.md are 6,000 B each and load on every turn. Context files raise inference cost by 20%+ without raising success; repository overviews help least and concrete instructions are what agents follow (ETH AGENTS.md study, 2026). OpenAI kept its agent-first repo's file to about 100 lines, used as a map.

Change: Keep the project role, toolchain one-liners, Gate, Commands and Hard rules. Drop the Layout tree and the per-feature/pr-loop narrative in favor of links to docs/groundwork.md and the pr-loop skill. groundwork-init's minimal file follows the same cap. Write GW-020.

Plan: docs/harness-upgrade.html

Probe: none — plugin text/stdlib change with no deployed or live behavior.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A plugin test fails first, then passes: CLAUDE.md and AGENTS.md are each <= 3,000 bytes, byte-identical, and contain `## Gate` and `## Hard rules`
- [ ] #2 The gate command and every hard rule survive the cut
- [ ] #3 groundwork-init says the instruction file it creates stays under the cap
- [ ] #4 GW-020 exists with its header and one INDEX.md line
<!-- AC:END -->
