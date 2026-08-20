# GW-001 — pr-loop: delivery as a state machine, PR as evidence ledger

**Status**: accepted · 2026-08-19

## Context

The previous delivery workflow used two independently-driven Claude sessions
(implementer opens a PR, reviewer comments, implementer fixes) with the human
relaying every step. Two problems: the human sat *inside* the control loop
making deterministic routing decisions ("implementation done → review it"),
and the PR filled with fine-grained agent-to-agent chatter — high
observability, low signal.

## Decision

1. **Orchestration moves from the human into one orchestrator session**
   (`/pr-loop <task-id>`), which drives an explicit state machine:
   IMPLEMENT → GATE → REVIEW → REPAIR → EVIDENCE. The human writes the spec
   and merges; everything between is agent- or eval-owned.
2. **Not Agent Teams, not an external harness.** implement→review→repair is a
   sequential feedback loop, not parallel collaboration; subagents (implementer
   in a worktree, pr-reviewer with fresh context) are the smallest mechanism
   that preserves role separation. The deterministic gate already exists — the
   eval suite — so no new verification machinery is built.
3. **Role separation is load-bearing**: the reviewer may not edit code, the
   implementer may not approve, the orchestrator may do neither. A reviewer
   that fixes what it finds and then approves collapses back to
   actor = evaluator, which is the failure the two-role design paid for.
4. **The PR records outcomes, not process**: one structured findings comment
   per review round, one final evidence pack (gate results, findings →
   resolutions, new eval cases, a runnable verification command). Agent
   deliberation stays in the session.
5. **The workflow evaluates itself**: one JSONL line per task
   (`evals/report/pr-loop-ledger.jsonl`) — review rounds, findings by
   severity, confirmed vs rejected, gate failures, human interventions.

## Consequences

- `TODO.md` at the repo root becomes the task queue (Hard rule 3 amended:
  it is the one sanctioned task file).
- Confirmed HIGH/MEDIUM findings feed the existing "every failure becomes a
  case" rule, so review quality compounds into the eval set.
- Circuit breaker at 3 review rounds — disputes escalate to the human with
  both positions; the loop never runs unbounded.
