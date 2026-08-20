---
name: groundwork-init
description: Adopt groundwork in the current repo — greenfield or brownfield. Scaffolds the pr-loop task queue, a Gate section, and optional enforcement hooks, additively and idempotently. Use when the user says /groundwork-init, "adopt groundwork", or "set up groundwork here".
---

# groundwork-init — adopt groundwork in this repo

Additive and idempotent: **never overwrite an existing file, never renumber
anything, never touch the README, the tests, or `specs/decisions/`.** Rerunning
on an initialized repo only fills gaps and reports "already present" for the
rest.

The full groundwork repo is checked out next to this plugin — scaffold files
are copied from `${CLAUDE_PLUGIN_ROOT}/..` (the marketplace clone), so no
network is needed.

## Steps

1. **Detect the situation.** Greenfield (no test suite, little/no src) vs
   brownfield (existing tests, CI, docs). This changes step 3 only.

2. **Task queue.** If `tasks/TODO.md` is missing, copy it and `tasks/DONE.md`
   from the marketplace clone (`ready.py` stays in the plugin — nothing to
   copy). If the repo already tracks tasks elsewhere (a milestone table,
   issues), do NOT convert anything — create the files alongside and note
   that pr-loop reads only this format.

3. **Gate.** If CLAUDE.md (create a minimal one if absent) has no `## Gate`
   section, add one:
   - Brownfield: list the repo's OWN existing verification commands (its test
     runner, linter, typecheck — read the repo to find them), each with its
     pass criterion. Do not invent new infrastructure.
   - Greenfield: offer the groundwork eval harness — copy `evals/run.py` and
     the `evals/{golden,adversarial,report}/` skeleton from the marketplace
     clone, and gate on `--suite invariant` (100%) + `--suite fast`
     (≥ `.eval-baseline.json`).
   pr-loop refuses to run without this section, so this step is the one that
   must not be skipped.

4. **Enforcement (ask first — this changes git behavior).** Offer to copy
   `.githooks/pre-commit` (runs the Gate before every commit) and set
   `git config core.hooksPath .githooks`, and to register the
   `.claude/hooks/` post-edit runner in `.claude/settings.json`. If the repo
   has its own pre-commit stack (husky, pre-commit.com), integrate with it
   instead of replacing it. Skip cleanly if declined — pr-loop still works;
   the gate just runs only inside the loop.

5. **Version marker.** Write `.groundwork-version` containing the upstream
   commit hash of the marketplace clone (`git -C ${CLAUDE_PLUGIN_ROOT}/..
   rev-parse HEAD`). Future syncs diff against this.

6. **Report.** One summary: what was created, what already existed, what was
   declined, and the two entry points — `/pr-loop next` and
   `python3 tasks/ready.py`.

## What NEVER happens here

- README.md is never created, edited, or templated — the project's front door
  belongs to the project (groundwork GW-003).
- `specs/decisions/` is never seeded — the project's ADR namespace starts
  empty and numbers itself; groundwork rationale is referenced as `GW-*`,
  never copied.
- Nothing existing is overwritten; no dependency is installed.
