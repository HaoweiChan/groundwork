# GW-004 — TODO.md holds only the working set; merged work moves to DONE.md
Status: accepted · 2026-08-20 · Amends: GW-002, GW-003

**Ruling**: `tasks/TODO.md` holds only `## Queue` and `## Debt`. Merged work
is replaced by a one-liner in `tasks/DONE.md`. `ready.py` ships once in the
plugin (`plugin/skills/pr-loop/scripts/`), never copied per-repo.
**Because**: every pr-loop invocation and human scan paid the token cost of
a Done section that only grows, and per-repo `ready.py` copies drifted
within a day of the first real project.
**Enforced by**: `plugin/skills/pr-loop/SKILL.md` § 1. SPEC (housekeeping
sweep) — advisory beyond that; no hook checks TODO.md's section contents.

---

## Context

After the first conversion of a real project (browser-agent), tasks/TODO.md
carried four concerns in one file: Queue, Debt, a Done section that grows
forever, and historical notes. Every pr-loop invocation and every human scan
paid the token cost of the whole file, dominated by the one section nobody
reads forward (Done). Separately, `ready.py` was being copied into each
project's `tasks/` — and drifted within a day (sec-10k held a two-versions-
stale copy), the exact per-repo-copy failure GW-003 removed for skills.

## Decisions

1. **Hot/cold split.** `tasks/TODO.md` holds only Queue and Debt — the
   working set, naturally bounded (debt gets promoted or culled). Merged
   work is replaced by a one-liner in `tasks/DONE.md`
   (`- <id> — <title> (<merge date>) — <refs>`): an index, not an archive —
   the narrative already lives in the ADRs/PR, the metrics in the ledger,
   the full block in git history.
2. **Progressive disclosure is a skill rule.** pr-loop's SPEC state greps
   the single target block and reads only that; the whole file is read only
   when a human orders the queue. SPEC also does the housekeeping sweep:
   any `status: pr` block whose PR has merged moves to DONE.md.
3. **ready.py ships in the plugin** (`plugin/skills/pr-loop/scripts/`),
   invoked from the repo root via `$CLAUDE_PLUGIN_ROOT`; per-repo copies are
   deleted. It resolves `Depends:` against TODO.md blocks plus DONE.md ids,
   and lists only Queue blocks as ready. Not being repo-side means CI and
   git hooks cannot call it — acceptable: it is a convenience view, never a
   gate.
4. **No debt aging rules yet** — current volume is a handful of small
   blocks; a staleness policy is speculative until the section demonstrably
   rots (YAGNI).

## Consequences

- groundwork-init scaffolds TODO.md + DONE.md and copies no scripts.
- Hierarchical tasks (subtasks) stay rejected: micro-tasks live in the
  session per the existing rule; `Depends:` is the only structure.
