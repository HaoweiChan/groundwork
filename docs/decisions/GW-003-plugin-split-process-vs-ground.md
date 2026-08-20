# GW-003 — process ships as a plugin; ground, state, and enforcement don't
Status: accepted · 2026-08-20 · Amends: GW-001, GW-002

**Ruling**: pr-loop, the four evidence-only agents, and eval/failure/cost
skills ship centrally as the groundwork plugin; the repo keeps the eval
harness, `specs/`, `tasks/`, CLAUDE.md, and all enforcement — hooks never ship as plugin content, and pr-loop runs the repo's declared `## Gate` section.
**Because**: clone-and-copy propagation drifted immediately (byte-copied
skills diverged, ADR numbering collided) and gave brownfield repos no
adoption path at all.
**Enforced by**: `.claude/settings.json` (plugin wiring) — advisory beyond
that; `/groundwork-init` is additive/idempotent, never touches README,
tests, or `specs/decisions/`.

---

## Context

groundwork propagated by clone-and-copy: descendants got byte-copies of
skills/agents that immediately started drifting (tasks/TODO.md location
diverged; a template ADR collided with a project's own ADR-002), updates
required manual byte-identical sync PRs, and brownfield repos had no adoption
path at all — the mechanisms assumed the template's directory layout and its
eval harness. A third symptom: freshly instantiated projects kept groundwork's
README as their own, so the project had no front door of its own.

## Decisions

1. **Process ships as a Claude Code plugin; ground stays in the repo.** The
   plugin (`plugin/`, self-hosted — this repo is its own marketplace, same
   pattern as ponytail) carries what is generic and should update centrally:
   the pr-loop skill, the four evidence-only agents (cold-reviewer,
   eval-adversary, spec-drift, pr-reviewer), eval-protocol / failure-triage /
   cost-discipline, and `/groundwork-init`. The repo keeps what is project
   state or project law: the eval harness and cases, `specs/`, `tasks/`,
   CLAUDE.md, and **all enforcement** — a plugin can be disabled silently, a
   hook versioned with the code cannot, so hooks are deliberately not plugin
   content.
2. **The gate is declared, not assumed.** pr-loop and the hooks run the
   commands in the repo CLAUDE.md's `## Gate` section instead of a hardcoded
   `evals.run` invocation. This is the single change that makes brownfield
   adoption real: an existing repo's gate is its existing test suite. pr-loop
   refuses to run without a `## Gate` section.
3. **Two adoption paths, one plugin.** Greenfield: clone the template
   (harness, hooks, layout pre-wired; settings.json already enables the
   plugin). Brownfield: install the plugin, run `/groundwork-init` — additive,
   idempotent, copies scaffold files from the marketplace clone (no network),
   asks before anything that changes git behavior, and never touches the
   README, the tests, or `specs/decisions/`.
4. **README belongs to the project.** The template README is instructions for
   instantiating groundwork and says "replace me"; the process reference that
   ships and stays is `docs/groundwork.md`. `/groundwork-init` never creates
   or edits a README.
5. **Versioning.** Plugin updates carry skills/agents; `.groundwork-version`
   records the upstream commit that scaffold files came from, so a project can
   diff deliberately instead of drifting silently. The pr-loop ledger moves to
   `tasks/pr-loop-ledger.jsonl` — `evals/report/` need not exist in a
   brownfield repo, `tasks/` always does after init.

## Consequences

- Descendant migration = enable the plugin, delete the vendored copies of the
  four skills + four agents (repo-local domain skills/agents stay), add a
  `## Gate` section, write `.groundwork-version`. Their ADR numbering and
  README are untouched — the collision class this fixes.
- The template repo self-hosts the plugin, so groundwork-the-project is the
  first consumer of groundwork-the-plugin.
- Skills now resolve as `groundwork:pr-loop` etc.; repo-local skills override
  plugin skills on name collision, which is the intended customization point.
