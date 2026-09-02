# groundwork decisions — index

One line per ADR, current ruling first. Amended/superseded ADRs are marked;
their file is kept for history but the ruling to follow is the amending one.

- GW-000 — the eval set is the spec, not prose requirements — enforced by PostToolUse invariant-suite hook + pre-commit eval gate
- GW-001 — delivery runs as an orchestrated state machine, not human relay — enforced by `plugin/skills/pr-loop/SKILL.md` (advisory) — *amended by GW-002, GW-003, GW-005, GW-009*
- GW-002 — a finding blocks the PR only if it's this task's problem — enforced by `plugin/skills/pr-loop/SKILL.md` § REVIEW; `ready.py` — *amended by GW-003, GW-004, GW-005, GW-009, GW-015, GW-017*
- GW-003 — process ships as a plugin; ground, state, and enforcement don't — enforced by plugin manifests and project-local hooks — *amended by GW-004, GW-010*
- GW-004 — TODO.md holds only the working set; merged work moves to DONE.md — enforced by `plugin/skills/pr-loop/SKILL.md` § 1. SPEC (advisory) — *amended by GW-017*
- GW-005 — pr-loop's PR is a bounded interface, not a shared transport — enforced by `plugin/skills/pr-loop/SKILL.md` § REVIEW/REPAIR/EVIDENCE, § PR body — *amended by GW-009, GW-015, GW-017*
- GW-006 — ADRs lead with the ruling, not the story — enforced by `docs/groundwork.md` § ADR format (advisory); invariant-suite case in descendant repos with an eval harness
- GW-007 — the orchestrator owns branch freshness against the PR's base (never assumed main); the gate runs on the synced tree — enforced by `plugin/skills/pr-loop/SKILL.md` § 4. GATE, § 8. EVIDENCE (advisory)
- GW-008 — report history is one line per run; full dumps only when they earn it — enforced by `evals/run.py` report-write logic; invariant-suite case in descendant repos with an eval harness
- GW-009 — pr-loop plans review deterministically and defaults to two model review calls — enforced by `plugin/tests/test_analyze.py` and pr-loop ANALYZE/REVIEW/VERIFY — *amended by GW-011, GW-015, GW-017*
- GW-010 — one `plugin/` root supports Claude Code and Codex with role parity — enforced by `plugin/tests/test_plugin_contracts.py` and both plugin validators
- GW-011 — pr-loop routes bounded work to the least expensive adequate subagent model — enforced by `plugin/tests/test_plugin_contracts.py` and the evidence ledger — *amended by GW-012, GW-014*
- GW-012 — pr-loop keeps its orchestrator at the high-capability floor and routes only bounded subagents downward — enforced by `plugin/tests/test_plugin_contracts.py` and `orchestrator_checks` — *amended by GW-014*
- GW-013 — root evals/src/specs stay clean project seed material; Groundwork self-tests live in plugin/tests — enforced by `plugin/tests/test_repository_boundary.py` and source-repo hooks
- GW-014 — model routing names capability floors, not product versions; newer stronger tiers qualify automatically — enforced by `plugin/tests/test_plugin_contracts.py` and pr-loop model checkpoints
- GW-015 — after call 2, pr-loop converges automatically instead of asking: BLOCKING findings repair, the rest demote to prioritized debt — enforced by `plugin/skills/pr-loop/SKILL.md` § 7 VERIFY (Convergence mode), § 8 EVIDENCE; `ready.py` — *amended by GW-017*
- GW-016 — the PR body opens with the task's spec, verbatim and immutable — enforced by `plugin/skills/pr-loop/SKILL.md` § PR body (advisory) · amends GW-005 — *amended by GW-017 (Task (verbatim) inside the six-section body)*
- GW-017 — pr-loop v4: one closed loop per task, two model calls, no rounds; findings block only with a repro; task state in Backlog.md; debt is one draft line — enforced by `plugin/tests/test_pr_loop_v4.py`, `plugin/skills/pr-loop/SKILL.md`, `plugin/agents/pr-reviewer.md`, `.github/pr_check.py` · amends GW-002, GW-004, GW-005, GW-009, GW-015
