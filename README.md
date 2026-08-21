# groundwork

**An eval-first project scaffold for the agent era.**

Agents write and maintain most of the code; what survives their handoffs is
executable checks and enforcement, not prose. groundwork gives a project four
layers — facts (`CLAUDE.md`/`AGENTS.md`), knowledge (skills), execution (review agents),
enforcement (hooks) — plus an eval harness that IS the spec and a cost-aware
`pr-loop` delivery state machine. Before model review it builds deterministic
change intelligence from the diff and an existing Graphify graph, enforces a
Ponytail surface preflight, and defaults to one adaptive review plus one delta
verification instead of an open-ended implementer↔reviewer loop.

Full architecture and process: **[docs/groundwork.md](docs/groundwork.md)**.
groundwork's own design decisions: `docs/decisions/GW-*.md`.

## Maintaining Groundwork

This repository deliberately keeps the project-facing `evals/`, `src/`, and
`specs/` scaffold clean. Groundwork's plugin contracts and regressions live in
`plugin/tests/` and run without third-party dependencies:

```bash
python3 -m unittest discover -s plugin/tests -p 'test_*.py'
```

Do not add plugin self-tests or generated run history to the root template eval
set. Those directories become the adopting project's specification after init.

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
2. Rewrite the project-specific parts of `CLAUDE.md` or `AGENTS.md` (name, Gate, layout).
3. Your decisions start at `specs/decisions/ADR-000` — the namespace is
   yours; groundwork's decisions stay in the groundwork repo as `GW-*`.

## Install the plugin

Groundwork ships one process-layer plugin with manifests for both Claude Code
and Codex. The initializer is additive and idempotent; it never touches your
README, tests, or existing ADR numbering.

### Claude Code

```
/plugin marketplace add HaoweiChan/groundwork
/plugin install groundwork@groundwork
/groundwork-init
```

### Codex

```bash
codex plugin marketplace add HaoweiChan/groundwork
codex plugin add groundwork@groundwork
```

Start a new Codex task after installation, then invoke `$groundwork-init`.
Codex loads the same skills and runs the four evidence roles through
no-history subagents. Initializer files are bundled inside the installed plugin,
so setup does not depend on the marketplace checkout remaining available. The
package follows OpenAI's
[Codex plugin structure](https://developers.openai.com/plugins/build/plugins#plugin-structure).

The initializer scaffolds `tasks/` (pr-loop queue), a `## Gate` section in the
host's project instruction file, optional enforcement hooks, and a
`.groundwork-version` marker. The delivery loop runs against whatever gate the
repo already has. On Codex, implementers work in a real Git worktree and
reviewers receive only the bounded review packet; neither inherits the
orchestrator's conversation.

## Use it

| Action | Claude Code | Codex |
|---|---|---|
| Deliver a task | `/pr-loop T10` | `$pr-loop T10` |
| Deliver the next ready task | `/pr-loop next` | `$pr-loop next` |
| Analyze without starting delivery | `/pr-loop analyze` | `$pr-loop analyze` |
| Cold review | `cold-reviewer` agent | `$cold-reviewer` |

`analyze` produces a read-only risk/impact/context packet without spending a
reviewer call. Before each subagent spawn, pr-loop also routes by task risk:
Claude uses Sonnet-level models for bounded routine work; Codex uses Luna-level
for mechanical work and Terra-level for ordinary implementation/focused review.
High-risk or full review requires Opus-level or stronger on Claude and Sol-level
or stronger on Codex. Every attempt, substitution, and outcome is written into
the PR evidence ledger. The orchestrator itself uses the same capability floor,
so newer stronger tiers qualify automatically; exact product versions are
resolved only at runtime.

## Updating a project

For Claude Code, update the marketplace/plugin through its plugin manager. For
Codex:

```bash
codex plugin marketplace upgrade groundwork
codex plugin add groundwork@groundwork
```

Start a new task after updating so Codex reloads the skills. Scaffold files
(eval runner, hooks, task queue) belong to the adopting repo after initialization;
update them deliberately and bump `.groundwork-version`. Rationale is referenced
(`GW-*` numbers), never copied into `specs/decisions/`.
