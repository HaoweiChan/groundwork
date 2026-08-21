# Project working rules

This is the **groundwork source repository** and also the seed copied into new
eval-first projects. Keep those roles separate: Groundwork's own executable
contracts live in `plugin/tests/`; root `src/`, `evals/`, and `specs/` remain a
clean project scaffold. Architecture rationale lives in `docs/groundwork.md`.

## Toolchain

- **groundwork** plugin (this repo's `plugin/`, dual-packaged through
  `.claude-plugin/` and `.codex-plugin/`) provides the process layer: pr-loop,
  four evidence-only roles, eval/failure/cost discipline skills, and
  groundwork-init. Claude loads native agents; Codex role skills spawn
  no-history subagents from the same canonical contracts. The plugin bundles
  initializer scaffold assets for installed-cache operation.
- **ponytail** plugin is enabled repo-wide via `.claude/settings.json` — laziest
  working solution, stdlib first, shortest diff. Applies to all code here.
- **graphify** is vendored as a project skill — use `/graphify` for architecture
  and file-relationship questions; once `graphify-out/` exists, treat such
  questions as graphify queries first.

## Layout

```
plugin/            dual Claude/Codex plugin — shared skills + canonical agent contracts
plugin/tests/      Groundwork's own stdlib-only contract and regression tests
.agents/plugins/   Codex repo marketplace
.claude/skills/    project-local skills only (domain knowledge, vendored graphify)
tasks/             TODO.md (Queue / Debt — the working set) + DONE.md (one-line index of merged work)
.claude/hooks/     enforcement — the only layer that can actually block
.githooks/         pre-commit Groundwork test gate (installed via core.hooksPath)
specs/             ONLY: 000-invariants.md, per-task contracts, decisions/ADR-*.md + decisions/INDEX.md
evals/              empty project-template eval harness; never store Groundwork self-tests here
prompts/           AI-collaboration record (auto-dumped raw/ + curated files)
src/               empty project-template implementation root
docs/              groundwork.md (process reference) + decisions/GW-* (template's own ADRs)
```

## Gate

The objective pass/fail for the Groundwork source repository:

```bash
python3 -m unittest discover -s plugin/tests -p 'test_*.py'
```

## Commands

```bash
python3 -m unittest discover -s plugin/tests -p 'test_*.py'
python3 plugin/skills/pr-loop/scripts/ready.py   # unblocked tasks in this source repo
```

## Hard rules

1. **Root `evals/` and `src/` are seed material, not Groundwork's self-test
   suite.** Put Groundwork regressions and contracts under `plugin/tests/`.
2. **Every new Groundwork failure becomes a test** under `plugin/tests/` before
   it is fixed. Watch the test fail first; a test never seen red proves nothing.
3. **specs/ holds only three kinds of files**: invariants, output contracts, ADRs
   (each ADR gets the 3-line header + `---` fold, groundwork GW-006; the ADR
   digest is `specs/decisions/INDEX.md`, one line per ADR).
   No plans in specs/ — task state lives only in `tasks/` (TODO.md working
   set + DONE.md index); ad-hoc task lists live in the session.
4. **No mocked results.** If a live dependency is unreachable, fail loudly; never
   fabricate output to make a run look green.
5. Commits go through the pre-commit test gate. `--no-verify` is for emergencies
   and must be explained in the commit message.
6. Commit subjects follow the existing form
   **`<scope-or-GW-NNN>: <lowercase imperative summary>`**. Inspect recent history
   before committing; do not switch to an unprefixed sentence-style subject.

## Per-feature loop

1. Plan mode → GW decision + new `plugin/tests/` contract/regression (test first)
2. Watch the new test fail
3. Implement (PostToolUse hook keeps running the plugin tests)
4. `cold-reviewer` subagent cold-reads → findings become regression tests
5. New tests into the suite → back to 3
6. Gate green → commit

For a full tasks/TODO.md task that should end in a PR, run the loop through
**`/pr-loop <task-id>`** on Claude Code or **`$pr-loop <task-id>`** on Codex
(`next` selects the next task): one orchestrator session
drives implement → deterministic analysis/Ponytail preflight → gate → adaptive
review → batched repair → delta verification. The default budget is two reviewer
calls; a third needs explicit human approval (groundwork GW-009). Before each
subagent spawn, route routine bounded work to Sonnet-level on Claude or
Luna-/Terra-level on Codex, explicitly using Opus-level-or-stronger /
Sol-level-or-stronger for high-risk or full review (GW-011). Keep the orchestrator
itself at that capability floor; newer stronger tiers qualify, and only bounded
subagents route downward (GW-012, GW-014). A finding blocks
only if it is in scope, evidence-backed, and confidence ≥0.80 — everything else
becomes Debt, not another round. The PR carries role-tagged structured findings
and an evidence pack, never agent chatter. Independent tasks
(`Depends:` satisfied — the plugin's `ready.py` lists them) can run as parallel pr-loop
sessions. Protocol: `plugin/skills/pr-loop/SKILL.md`.

`/pr-loop analyze` (Claude) or `$pr-loop analyze` (Codex) produces the read-only
review plan without starting delivery.

## Adding a task

The following applies after this repository is instantiated as a project; it
does not authorize Groundwork maintainers to use the seed directories for plugin tests.

1. `src/<task>/` with an `eval_adapter.py` exposing `run_case(case) -> {"passed": bool, ...}`
2. A domain-knowledge skill in `.claude/skills/<task>-domain/`
3. A contract spec `specs/0NN-<task>-contract.md`
4. Golden + adversarial cases tagged with `"task": "<task>"`
