# groundwork decisions — index

One line per ADR, current ruling first. Amended/superseded ADRs are marked;
their file is kept for history but the ruling to follow is the amending one.

- GW-000 — the eval set is the spec, not prose requirements — enforced by PostToolUse invariant-suite hook + pre-commit eval gate
- GW-001 — delivery runs as an orchestrated state machine, not human relay — enforced by `plugin/skills/pr-loop/SKILL.md` (advisory) — *amended by GW-002, GW-003, GW-005*
- GW-002 — a finding blocks the PR only if it's this task's problem — enforced by `plugin/skills/pr-loop/SKILL.md` § Scope boundary, § REVIEW; `ready.py` — *amended by GW-003, GW-004, GW-005*
- GW-003 — process ships as a plugin; ground, state, and enforcement don't — enforced by `.claude/settings.json` (advisory beyond that) — *amended by GW-004*
- GW-004 — TODO.md holds only the working set; merged work moves to DONE.md — enforced by `plugin/skills/pr-loop/SKILL.md` § 1. SPEC (advisory)
- GW-005 — pr-loop's PR is a bounded interface, not a shared transport — enforced by `plugin/skills/pr-loop/SKILL.md` § REVIEW/REPAIR/EVIDENCE, § PR body, § PR comment identity
- GW-006 — ADRs lead with the ruling, not the story — enforced by `docs/groundwork.md` § ADR format (advisory); invariant-suite case in descendant repos with an eval harness
