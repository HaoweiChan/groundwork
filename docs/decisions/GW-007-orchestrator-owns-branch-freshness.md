# GW-007 — the orchestrator owns branch freshness against the PR's base; the gate runs on the tree that will merge
Status: accepted · 2026-08-20 · Amends: GW-001, GW-005

**Ruling**: every GATE starts by merging the PR's base branch (`baseRefName`, never
assumed `main`) into the task branch — never rebase; conflicts go to the implementer,
id collisions are reconciled; the gate runs on the synced tree, EVIDENCE needs `mergeable`.
**Because**: parallel pr-loop sessions merge into the base while others run — the
loop was blind to this and a gate passed on a stale base proves nothing.
**Enforced by**: `plugin/skills/pr-loop/SKILL.md` § 4. GATE (branch freshness),
§ 8. EVIDENCE; `Base:` line in the PR body template — advisory beyond that.

---

## Context

pr-loop's orchestrator attention was entirely on the reviewer↔implementer
loop. Nothing in the state machine said what happens when the base moves under
a task branch — which is the normal case once `Depends:` lets several
sessions run in parallel. Observed the day parallelism started: a template
ADR numbered ADR-021 landed while a sibling branch was also creating ADR-021
(GitHub reported MERGEABLE — different filenames — but the repo would have
had two ADR-021s and a red hygiene case after merge); T13's TODO.md edits
landed under a branch rewriting the same file. Both were caught by a human
reviewer, not by the loop.

## Decision

1. Freshness is checked at the start of **every** GATE, not once at PR
   creation: fetch, compare, `git merge origin/<base>` where base is the
   PR's `baseRefName` (or the branch the task was cut from, pre-PR) — task
   branches do not necessarily target `main`. Merge rather than
   rebase so the sync never requires a force-push (which the safety
   classifier blocks and which rewrites a branch others may have fetched).
2. Textual conflicts are implementation work — the orchestrator relays them
   to the implementer like any other repair item. The reviewer never
   resolves conflicts (role separation), and neither does the orchestrator.
3. Semantic collisions are the orchestrator's to detect because git cannot:
   after each sync, diff what main brought against what the branch adds in
   shared namespaces (ADR numbers, task ids, eval case ids, TODO.md blocks)
   and reconcile on the branch (renumber, re-split, re-index).
4. The gate is meaningful only on the tree that will actually merge, so it
   runs after the sync. The PR body records `Base: <base>@<sha>` per sync;
   EVIDENCE does a final sync and requires the PR to be `mergeable` before
   handing to the human.

## Consequences

- A sibling merge costs the in-flight loop one extra gate run, not a
  post-merge surprise.
- Round counts are unaffected: a sync is not a review round; conflicts
  relayed to the implementer ride the current round's repair.
