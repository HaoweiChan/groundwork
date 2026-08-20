# groundwork

**An eval-first project scaffold for the agent era.**

Agents write and maintain most of the code; what survives their handoffs is
executable checks and enforcement, not prose. groundwork gives a project four
layers — facts (`CLAUDE.md`), knowledge (skills), execution (review agents),
enforcement (hooks) — plus an eval harness that IS the spec and a `/pr-loop`
delivery state machine that keeps humans out of the implementer↔reviewer
relay loop.

Full architecture and process: **[docs/groundwork.md](docs/groundwork.md)**.
groundwork's own design decisions: `docs/decisions/GW-*.md`.

## Greenfield — start a project from the template

```bash
git clone <this-repo> my-project && cd my-project
git config core.hooksPath .githooks   # enable the pre-commit eval gate
python3 -m evals.run --suite fast     # sanity: runner works (no cases yet)
```

Then, before anything else:

1. **Replace this README.** The README belongs to *your project* — what it
   is, how to run it. A project whose README still describes groundwork has
   no front door. The process doc you keep is `docs/groundwork.md`.
2. Rewrite the project-specific parts of `CLAUDE.md` (name, Gate, layout).
3. Your decisions start at `specs/decisions/ADR-000` — the namespace is
   yours; groundwork's decisions stay in the groundwork repo as `GW-*`.

## Brownfield — adopt groundwork in an existing repo

Install the plugin and run the initializer — it is additive and idempotent,
and never touches your README, tests, or existing ADR numbering:

```
/plugin marketplace add HaoweiChan/groundwork
/plugin install groundwork@groundwork
/groundwork-init
```

`/groundwork-init` scaffolds `tasks/` (pr-loop queue), a `## Gate` section in
CLAUDE.md pointing at *your existing* test commands, optional git hooks, and
a `.groundwork-version` marker. The pr-loop state machine runs against
whatever gate your repo already has.

## Updating a project

Skills and agents update through the plugin. Scaffold files (evals runner,
hooks, `tasks/ready.py`) are yours after instantiation — pull upstream
changes deliberately and bump `.groundwork-version`. Rationale is referenced
(`GW-*` numbers), never copied into your `specs/decisions/`.
