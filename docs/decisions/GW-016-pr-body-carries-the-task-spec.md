# GW-016 — the PR body opens with the task's spec, verbatim and immutable
Status: accepted · 2026-08-27 · Amends: GW-005

**Ruling**: The rolling PR body's first section after the title is `### Task` —
the tasks/TODO.md block (Origin, Depends, Priority, Spec, Acceptance) copied
verbatim at PR creation and never edited afterward. Everything below it rolls.
**Because**: real PRs showed the rounds and failures clearly but not what the
task set out to solve or where it came from — the why lived only in TODO.md,
which the block leaves on merge.
**Enforced by**: `plugin/skills/pr-loop/SKILL.md` § PR body — advisory.

---

## Context

By browser-agent PR #60 the evidence-pack format was doing its job: rounds,
important failures, gate state, and trace pointers all legible in seconds.
What a reader could NOT recover from the PR was the task's original purpose —
the goal line compresses "what done means" but not the problem, and the task
block that carries the why (`Spec:` is literally "what and why", `Origin:`
names the PR/finding that created a debt-born task) lives in tasks/TODO.md,
which the block leaves on merge (GW-004 moves it to a DONE.md one-liner). The
PR — the durable artifact a reviewer or interviewer actually opens — had
iteration history without intent.

## Decision

Seed `### Task` into the PR body at creation, verbatim from the block, and
declare it immutable for the PR's life: later body rewrites (rounds, failures,
verification) never touch it. If the spec itself changes mid-flight, that is a
human spec decision — recorded as a dated addendum line under the section,
never by editing the original text.

## Consequences

- Debt-born tasks show their full lineage in the PR (`Origin: PR #N R#
  (converged)` → the finding → the parent PR) with no extra tooling.
- The DONE.md one-liner can stay one line — the PR now carries the fuller
  record it points to.
