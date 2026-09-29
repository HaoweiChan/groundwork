---
id: TASK-3
title: Analyzer flags weakened evals and baseline moves as high risk
status: To Do
assignee: []
created_date: '2026-09-29 15:56'
labels:
  - guardrail
  - analyzer
dependencies: []
documentation:
  - docs/harness-upgrade.html
priority: high
ordinal: 3000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
`classify_risk` only asks whether some eval file changed, so deleting or editing a golden case reads as healthy and `.eval-baseline.json` edits are invisible. Detecting edits to test files catches most reward hacking (EvilGenie); RL post-training raised exploit rates from 0.6% to 13.9% in one benchmark.

Change: New risk reason `eval-weakened` at level high when the diff deletes or modifies an existing file under `evals/golden/`, `evals/adversarial/`, `tests/` or `plugin/tests/`, or touches `.eval-baseline.json`. Added cases stay unflagged. Flagged files join `review.targets`. Write GW-019.

Plan: docs/harness-upgrade.html

Probe: none — plugin text/stdlib change with no deployed or live behavior.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 test_analyze.py fails first, then passes: deleting a golden case gives level high with reason `eval-weakened`
- [ ] #2 Modifying `.eval-baseline.json` gives level high with reason `eval-weakened`
- [ ] #3 Adding a new case under `evals/golden/` does not add `eval-weakened`
- [ ] #4 Flagged files appear in `review.targets`
- [ ] #5 The pr-loop-analysis-domain skill lists the reason; GW-019 exists with its header and one INDEX.md line
<!-- AC:END -->
