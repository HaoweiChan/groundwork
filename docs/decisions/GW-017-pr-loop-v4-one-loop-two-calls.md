# GW-017 — pr-loop v4: one closed loop per task, two model calls, no rounds
Status: accepted · 2026-09-03 · Amends: GW-002, GW-004, GW-005, GW-009, GW-015

**Ruling**: pr-loop keeps its name and becomes a closed control loop per task:
implement → deterministic gate → live probe → one independent verification →
at most one repair → one delta verification → human. Findings block only with a
reproduction and only under acceptance, drift, or wrong output; prose never
blocks. Debt is one draft line with a case or run id. Task state moves from
`tasks/TODO.md` to Backlog.md, read one task at a time.
**Because**: two real deliveries (browser-agent, sec-10k-extract, 2026-08-16 →
08-30) measured the open-round design: 198 rounds over 69 tasks, 851 findings
of which 31–42% were about prose, 74 circuit-breaker interruptions answered
"continue", a 427 KB TODO.md read at every session start, and the acceptance's
live half left "not run" in 36 of 40 loop PRs — the demos then failed on
exactly that half.
**Enforced by**: `plugin/tests/test_pr_loop_v4.py`; `plugin/skills/pr-loop/SKILL.md`;
`plugin/agents/pr-reviewer.md`; `.github/pr_check.py` (PR shape).

---

## Why "loop" stays

The current vocabulary for this shape is *loop engineering*: an agentic
pipeline with a sensor (the gate and the probe), an actuator (the implementer),
and an independent controller (the verifier) closed into one feedback loop
that runs without a human inside it. That is what pr-loop is and what it
advertises — a self-supervised delivery pipeline in which the executor never
grades its own work. The loop iterates over tasks. It does not iterate over
rounds inside a task; v4 makes that distinction the design rather than a
budget knob.

## Context — what the measurements said

- **Rounds did not converge.** Median 4 rounds per task, up to 7. Ledger notes
  record "rounds 4–6 were prose only" and "three of five rounds spent on
  wall-clock ceilings, not the feature". The same defect class regenerated
  across rounds (R2 → R9 → R16 → R20) because each repair was allowed to
  reopen the whole surface.
- **Prose was a blocking condition.** GW-002/GW-015 let "a published claim is
  dishonest" block. Nobody reads the ADRs; the finding class was unbounded.
- **The live half was never in the loop.** Gate = offline suites at $0.
  Acceptance clauses that needed a deployment were deferred "post-merge" and
  reopened under new task ids (M10 → M29 → M34 → M36), which is the exact
  "same problem, another PR" the owner wanted to stop.
- **Debt was a full task block per LOW finding.** 206 blocks, 35% ever closed;
  every session read all of them.
- **Parallel sessions collided** on ids and ADR numbers; the fix is elsewhere
  (Backlog.md scans branches when minting ids) but the loop no longer needs to
  arbitrate it.

## Decision

1. **Two calls, no breaker.** Call 1 verifies acceptance, drift, and wrong
   output. If anything blocks, one batched repair, then call 2 verifies the
   delta. Anything still open goes to the human as `Decision: not met`. No
   convergence mode, no circuit breaker, no clarify route.
2. **Repro or nothing.** A finding without a runnable repro never blocks and is
   not filed. Prose, naming, documentation, and style are never findings.
3. **Probe is a state.** A task declares `Probe: <command> · budget · reps` or
   `Probe: none — <reason>`. The probe runs after the gate, before the
   verifier, and its run ids go on the PR's `Live:` line. A task without a
   checkable acceptance is not eligible for the loop.
4. **Same task id until the probe is green.** A post-merge probe closes the
   task that opened it; it never spawns a new task for the same problem.
5. **Debt is one draft line.** `backlog task create --draft` with a `case <id>`
   or `run <id>` acceptance. No Spec, no Acceptance text, no priority ceremony.
   Drafts are invisible to `task list`; a human promotes and specifies later.
6. **Task store is Backlog.md.** `tasks/TODO.md`, `tasks/DONE.md`, and
   `ready.py` retire. SPEC reads `backlog task list --ready --plain` and one
   `backlog task view`. Session start cost drops from ~106k tokens to ~1k on
   the measured repos.
7. **One review artifact per PR.** `tasks/reviews/pr<N>.json`, rewritten after
   call 2. No per-round resolution and verification files.
8. **PR body is the six-section shape** checked by `.github/pr_check.py`, the
   same for pr-loop and for hand-written PRs.

## Alternatives considered

- **Keep GW-015 convergence and only drop the prose clause.** Rejected: the
  breaker still fired on repair-regressions, and "BLOCKING" still admitted a
  false published claim. Half the cost stayed.
- **Drop the reviewer entirely; gate + human.** Rejected by the owner: the
  executor is often a weaker model and must be checked by a stronger one for
  drift and self-reporting. One call keeps that; rounds do not add to it.
- **Keep TODO.md but one file per block.** Viable, but re-implements ready
  filtering, archiving, and id allocation that Backlog.md already ships with
  Claude Code and Codex MCP support.

## What this does not claim

The verifier still cannot see deployed behavior the probe does not exercise;
`Not verified:` in the PR body is where that is said. Backlog.md adds an npm or
bun dependency to adopting repos. The two measured repos are not migrated by
this decision; migration is a separate one-off script per repo.
