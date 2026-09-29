---
id: TASK-4
title: pr_check.py validates the verifier's review JSON
status: To Do
assignee: []
created_date: '2026-09-29 15:56'
labels:
  - guardrail
  - pr-loop
dependencies: []
documentation:
  - docs/harness-upgrade.html
priority: high
ordinal: 4000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
'A finding without a repro never blocks' is the loop's central output rule and lives only in prose (pr-reviewer.md, pr-loop § VERIFY). Only 4-16% of written rules enforce themselves (Marmelab 2026). The verifier is the loop's one model-based sensor, so its output should pass a computational check.

Change: `pr_check.py --review <file>` checks `tasks/reviews/pr<N>.json`: result and severity enums; a required `question` field (acceptance | drift | wrong-output); a non-empty `repro` on every blocking finding; REQUEST_CHANGES only with at least one blocking finding; in verify mode, one record per standing id. The PR workflow runs it on changed review files; the orchestrator runs it before REPAIR and counts rejections in the ledger as `review_check_failures`.

Plan: docs/harness-upgrade.html

Probe: none — plugin text/stdlib change with no deployed or live behavior.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 test_pr_check.py fails first, then passes: a blocking finding with an empty repro is rejected with a message naming the finding id
- [ ] #2 A valid review-mode file and a valid verify-mode file are accepted
- [ ] #3 A verify-mode result missing a standing finding id is rejected
- [ ] #4 pr-reviewer.md and pr-loop § VERIFY require the `question` field; pr-check.yml runs `--review` on changed `tasks/reviews/*.json`
- [ ] #5 GW-019 lists `pr_check.py --review` under Enforced by
<!-- AC:END -->
