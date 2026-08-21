# Project working rules

Eval-first repo, built on **groundwork**. Tasks live under `src/<task>/`.
**The eval set IS the spec.** groundwork targets problems where requirements
are clear but correctness is hard to define up front — so correctness is encoded
as executable invariants and metrics, not prose. Architecture rationale lives in
docs/groundwork.md; this file is the working contract. README.md belongs to the
project, not to groundwork — replace it when instantiating the template.

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
.agents/plugins/   Codex repo marketplace
.claude/skills/    project-local skills only (domain knowledge, vendored graphify)
tasks/             TODO.md (Queue / Debt — the working set) + DONE.md (one-line index of merged work)
.claude/hooks/     enforcement — the only layer that can actually block
.githooks/         pre-commit eval gate (installed via core.hooksPath)
specs/             ONLY: 000-invariants.md, per-task contracts, decisions/ADR-*.md + decisions/INDEX.md
evals/golden/      hand-labeled cases (JSON, one per case)
evals/adversarial/ cases known or designed to break the pipeline
evals/report/      history.jsonl (one line per run) + full reports only for requested/`all`/red runs and cited reports of record
prompts/           AI-collaboration record (auto-dumped raw/ + curated files)
src/<task>/        implementation + eval_adapter.py per task
docs/              groundwork.md (process reference) + decisions/GW-* (template's own ADRs)
```

## Gate

The objective pass/fail for this repo. pr-loop, the hooks, and any reviewer
run exactly these, in order:

```bash
python3 -m evals.run --suite invariant   # pass: 100%
python3 -m evals.run --suite fast        # pass: score ≥ .eval-baseline.json
```

## Commands

```bash
python3 -m evals.run --suite all               # everything, writes report
python3 -m evals.run --suite fast --update-baseline   # deliberate baseline move
python3 plugin/skills/pr-loop/scripts/ready.py   # unblocked tasks in this source repo
```

## Hard rules

1. **Never edit `.eval-baseline.json` by hand** and never `--update-baseline` just to
   make the pre-commit gate pass. A baseline move is a decision — record why in an ADR.
2. **Every new failure becomes a case** in `evals/adversarial/` before it is fixed.
   Watch the new case fail first; an eval you've never seen red proves nothing.
3. **specs/ holds only three kinds of files**: invariants, output contracts, ADRs
   (each ADR gets the 3-line header + `---` fold, groundwork GW-006; the ADR
   digest is `specs/decisions/INDEX.md`, one line per ADR).
   No plans in specs/ — task state lives only in `tasks/` (TODO.md working
   set + DONE.md index); ad-hoc task lists live in the session.
4. **No mocked results.** If a live dependency is unreachable, fail loudly; never
   fabricate output to make a run look green.
5. Commits go through the pre-commit eval gate. `--no-verify` is for emergencies
   and must be explained in the commit message.

## Per-feature loop

1. Plan mode → ADR + new invariant/eval cases (eval first)
2. Watch the new cases fail
3. Implement (PostToolUse hook keeps running the invariant suite)
4. `cold-reviewer` subagent cold-reads → its findings become adversarial cases
5. New cases into the eval set → back to 3
6. Eval gate green → commit

For a full tasks/TODO.md task that should end in a PR, run the loop through
**`/pr-loop <task-id>`** on Claude Code or **`$pr-loop <task-id>`** on Codex
(`next` selects the next task): one orchestrator session
drives implement → deterministic analysis/Ponytail preflight → gate → adaptive
review → batched repair → delta verification. The default budget is two reviewer
calls; a third needs explicit human approval (groundwork GW-009). Before each
subagent spawn, route routine bounded work to Sonnet on Claude or Luna/Terra on
Codex, explicitly using Opus/Sol for high-risk or full review (GW-011). A finding blocks
only if it is in scope, evidence-backed, and confidence ≥0.80 — everything else
becomes Debt, not another round. The PR carries role-tagged structured findings
and an evidence pack, never agent chatter. Independent tasks
(`Depends:` satisfied — the plugin's `ready.py` lists them) can run as parallel pr-loop
sessions. Protocol: `plugin/skills/pr-loop/SKILL.md`.

`/pr-loop analyze` (Claude) or `$pr-loop analyze` (Codex) produces the read-only
review plan without starting delivery.

## Adding a task

1. `src/<task>/` with an `eval_adapter.py` exposing `run_case(case) -> {"passed": bool, ...}`
2. A domain-knowledge skill in `.claude/skills/<task>-domain/`
3. A contract spec `specs/0NN-<task>-contract.md`
4. Golden + adversarial cases tagged with `"task": "<task>"`
