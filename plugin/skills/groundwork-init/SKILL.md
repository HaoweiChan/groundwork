---
name: groundwork-init
description: Adopt groundwork in the current repo — greenfield or brownfield. Scaffolds the pr-loop task queue, a Gate section, and optional enforcement hooks, additively and idempotently. Use for /groundwork-init or $groundwork-init, "adopt groundwork", or "set up groundwork here".
---

# groundwork-init — adopt groundwork in this repo

Additive and idempotent: **never overwrite an existing file, never renumber
anything, never touch the README, the tests, or `specs/decisions/`.** Rerunning
on an initialized repo only fills gaps and reports "already present" for the
rest.

Resolve `<groundwork-plugin-root>` as the parent of the `skills/` directory that
contains this `SKILL.md`. Always use
`<groundwork-plugin-root>/assets/scaffold` as the scaffold source, whether the
plugin came from a Git marketplace or an installed cache. Resolve this location
from the skill file path — never from a host-specific environment variable. Stop
with a missing-package error if the bundled scaffold is absent; do not improvise
files. No network is needed.

## Steps

1. **Detect the situation.** Greenfield (no test suite, little/no src) vs
   brownfield (existing tests, CI, docs). This changes step 3 only.

2. **Task store.** If `backlog/config.yml` is missing, run `backlog init
   --defaults` (Backlog.md, `npx -y backlog.md` when the CLI is not installed).
   pr-loop reads one task at a time through `backlog task list --ready --plain`
   and `backlog task view <id> --plain`; debt lives in `backlog/drafts/`. If the
   repo already tracks tasks elsewhere (issues, a milestone table), do NOT
   convert anything — initialize alongside and note that pr-loop reads only
   Backlog.md. A repo still carrying the retired `tasks/TODO.md` block format
   migrates its `[status: todo]` blocks with
   `python3 <this-skill-dir>/scripts/migrate_todo.py tasks/TODO.md` (prints
   the `backlog task create` commands; add `--run` to execute them), then
   deletes `tasks/TODO.md` and `tasks/DONE.md` — history keeps them.

3. **Gate.** Use the host's project instruction file: `AGENTS.md` on Codex,
   `CLAUDE.md` on Claude Code. If it is absent, create a minimal one; if its
   `## Gate` section is absent, add one:
   - Brownfield: list the repo's OWN existing verification commands (its test
     runner, linter, typecheck — read the repo to find them), each with its
     pass criterion. Do not invent new infrastructure.
   - Greenfield: offer the groundwork eval harness — copy `evals/run.py` and
     the `evals/{golden,adversarial,report}/` skeleton from the bundled
     clone, and gate on `--suite invariant` (100%) + `--suite fast`
     (≥ `.eval-baseline.json`). `evals/report/history.jsonl` is created on
     the first run (one line, no other change).
   pr-loop refuses to run without this section, so this step is the one that
   must not be skipped.

4. **Enforcement (ask first — this changes git behavior).** Offer to copy
   `.githooks/pre-commit` (runs the Gate before every commit) and set
   its executable bit before `git config core.hooksPath .githooks`, and to
   register the host's project
   PostToolUse hook (`.claude/hooks/` plus settings on Claude Code, project Codex
   hooks when available). If the repo
   has its own pre-commit stack (husky, pre-commit.com), integrate with it
   instead of replacing it. Skip cleanly if declined — pr-loop still works;
   the gate just runs only inside the loop.
   Also offer the PR shape: copy `.github/PULL_REQUEST_TEMPLATE.md`,
   `.github/pr_check.py`, `.github/workflows/pr-check.yml`, and
   `.githooks/commit-msg` from the scaffold (skip any that exist). The
   workflow fails a PR whose title is not
   `<type>(<scope>)?: <lowercase summary>` or whose body is missing one of the
   six sections; the commit-msg hook holds commit subjects to the same title
   rule — one shape for every author, human or agent.

5. **Toolchain (ask first — this enables plugins and adds a skill).** Offer
   two optional additions, each independently declinable:
   - **Plugin wiring**: merge `assets/scaffold/.claude/plugins-fragment.json`
     (groundwork + ponytail marketplaces and enabledPlugins) into the repo's
     `.claude/settings.json` — create the file if absent, MERGE keys if it
     exists, never overwrite an existing entry. The host will still ask the
     user to approve each plugin on next open; this step only declares them
     at project scope so every future session and teammate gets the prompt.
   - **Graphify skill**: copy `assets/scaffold/.claude/skills-graphify` to
     `.claude/skills/graphify` (skip if the path exists or the user has it
     globally). pr-loop's analyzer consumes `graphify-out/` only when present
     either way — declining costs nothing but the richer analysis packet.
   Skip both cleanly if declined; pr-loop works without them.

6. **Version marker.** Write `.groundwork-version` containing the upstream
   commit hash of the resolved Git marketplace checkout. If the installed plugin
   is not inside a Git checkout, use the manifest version instead. Future syncs
   compare against this marker.

7. **Report.** One summary: what was created, what already existed, what was
   declined, and the host's two entry points — `/pr-loop next` on Claude Code or
   `$pr-loop next` on Codex, plus the ready script resolved from the skill path.

## Upgrading a repo initialized before 0.6

A repo that adopted groundwork while pr-loop still read `tasks/TODO.md`
(plugin < 0.6.0, `.groundwork-version` older than GW-017) upgrades in one
branch, additively, in this order. Say "upgrade groundwork" to run it.

1. **Task store.** `backlog init --defaults` (or `npx -y backlog.md init
   --defaults`) if `backlog/config.yml` is missing. Then migrate the open
   blocks: `BACKLOG="npx -y backlog.md" python3
   <this-skill-dir>/scripts/migrate_todo.py tasks/TODO.md --run`. Queue
   `[status: todo]` blocks become tasks, Debt blocks become drafts, old ids
   survive as `--ref`. `pr`/`in-progress`/`done` blocks are not migrated —
   finish or close them by hand. Then `git rm tasks/TODO.md tasks/DONE.md`;
   git history keeps every block. Keep `tasks/pr-loop-ledger.jsonl` and
   `tasks/reviews/`.
2. **PR shape.** Copy `.github/PULL_REQUEST_TEMPLATE.md`, `.github/pr_check.py`,
   `.github/workflows/pr-check.yml`, and `.githooks/commit-msg` from the
   scaffold; `chmod +x .githooks/commit-msg`.
3. **Instructions.** In `CLAUDE.md` / `AGENTS.md`: replace every mention of
   `tasks/TODO.md`, `tasks/DONE.md`, and `ready.py` with the Backlog.md
   commands (`backlog task list --ready --plain`, `backlog task view <id>
   --plain`); replace the pr-loop paragraph with the v4 shape (two model
   calls, probe, `Decision: not met`); add the one-shape commit/PR title rule.
   Do not rewrite anything else in those files.
4. **Tasks need a probe.** Every migrated task carries `Probe: none — migrated
   from TODO.md`. Before running `/pr-loop` on one, edit that line to a real
   probe command with a budget, or leave `none` with a structural reason.
5. **Version marker.** Overwrite `.groundwork-version` with the new upstream
   commit hash. Commit as `chore(groundwork): upgrade to pr-loop v4` and open
   the PR with the six-section body.

## What NEVER happens here

- README.md is never created, edited, or templated — the project's front door
  belongs to the project (groundwork GW-003).
- `specs/decisions/` is never seeded — the project's ADR namespace starts
  empty and numbers itself; groundwork rationale is referenced as `GW-*`,
  never copied.
- Nothing existing is overwritten; no dependency is installed.
