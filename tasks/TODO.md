# Tasks — pr-loop queue

Format and rules: the groundwork plugin's `pr-loop` skill. Two sections only —
merged work moves to `tasks/DONE.md` as one-liners. Blocks take an optional
`Priority: P1|P2|P3` line (mandatory on Debt, default P2); `ready.py` sorts
ready tasks by (priority, id). List unblocked tasks:
`python3 "$CLAUDE_PLUGIN_ROOT"/skills/pr-loop/scripts/ready.py` (from repo root).

## Queue

## Debt
