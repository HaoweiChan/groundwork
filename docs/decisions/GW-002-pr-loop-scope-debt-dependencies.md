# GW-002 — pr-loop: scope boundary, debt, and task dependencies

**Status**: accepted · 2026-08-19
**Extends**: GW-001 (pr-loop delivery state machine)

## Context

The first real pr-loop run (browser-agent PR #12, milestone M8) took **6
review rounds** before merge readiness. The transcript shows two structural
causes, not a broken loop: (a) each round spawned a fresh-context reviewer
who re-falsified the **entire diff**, so every round surfaced a new class of
finding — rounds 1–2 found real metric defects, rounds 3+ found only
declaration-vs-code drift (a stale methodology paragraph, an ADR row count),
each costing a full repair round; (b) severity was the only trigger — a
finding had no way to be "real but not this PR's problem".

Separately: tasks had no dependency information, so only one delivery session
could safely run at a time; and `tasks/` held a queue with no place for the
work a PR deliberately declines.

## Decisions

1. **Scope boundary on blocking.** A finding triggers REPAIR only if it is
   HIGH/MEDIUM **and** violates the task's acceptance criteria, turns the
   gate red, or makes a published number/claim dishonest. Everything else —
   regardless of severity — is logged as debt. Honesty stays blocking
   because this scaffold treats published-but-wrong as the worst failure
   class (GW-000); PR #12's R14 (a known-wrong ground truth whose committed
   raw report reads as verified-correct) is the canonical in-scope example,
   its R12/R13 doc drift the canonical debt.
2. **Round 1 sweeps, later rounds don't.** Round 2+ reviewers see only the
   repair diff plus standing findings. An unbounded falsification loop over
   a full diff never converges — the M8 trajectory is the evidence.
3. **Debt is a first-class task.** `tasks/TODO.md` gains three sections —
   `## Queue` / `## Debt` / `## Done` — sharing one `T<N>` id sequence. A
   debt block is a normal task block plus `Origin: PR #<n> <finding-id>`;
   promoting it is moving it into Queue. Mid-implementation scope overflow
   follows the same rule: log it, stay on spec.
4. **Dependencies enable parallel sessions.** Task blocks gain an optional
   `Depends: T3, T7` field; pr-loop refuses a task with unmet deps;
   `tasks/ready.py` (stdlib, ~60 lines) prints ready vs blocked so the human
   knows how many sessions to open. Worktree branches `task/<id>` keep
   parallel runs isolated. A full dependency-graph engine (task-master
   style) was considered and rejected — the field plus one script is the
   entire requirement.

## Consequences

- The ledger line tracks `debt_logged` alongside `repaired`/`rejected`, so
  the scope boundary itself is measurable (a loop that logs everything as
  debt and merges junk shows up in the numbers).
- Reviewer findings tables mark each row `repair` or `debt` — the routing
  decision is part of the audit record.
- Expected effect on an M8-shaped task: ~2 rounds instead of 6, with the
  drift findings surviving as Queue-able debt instead of round fuel.
