# groundwork — architecture

The agent-facing process doc. It ships with every groundwork project and is
the reference CLAUDE.md points at; the project's README belongs to the
project, never to groundwork.

## The idea

Most of the code in a groundwork project will be written, reviewed, and
maintained by AI agents. What survives agent handoffs is not tribal knowledge
or session memory — it is architecture, executable checks, and enforcement.
For problems with no public ground truth (extraction, agents, pipelines,
anything where "correct" is a judgment call), you lay your own ground — the
eval set.

Prose specs like "the output must be correct" are unfalsifiable, and an agent
told "please be careful" will drift. groundwork replaces both:

- **The eval set IS the spec.** Correctness lives in executable invariants and
  golden/adversarial cases, not in requirement documents. If a property isn't
  backed by a case that can go red, it doesn't exist.
- **Advice doesn't bind agents; enforcement does.** CLAUDE.md is advice. Hooks
  are law. Anything that must never happen is enforced by a hook that blocks,
  not a sentence that asks.

## Architecture — four layers, no overlap

Each layer answers one question. Nothing appears in two layers.

| Layer | Lives in | Answers | Binding? |
|---|---|---|---|
| **Facts** | `CLAUDE.md` / `AGENTS.md` | What is invariantly true here? (structure, commands, hard rules) | advisory |
| **Knowledge** | skills | How do we do X well? (loaded on demand, zero resident context) | advisory |
| **Execution** | agents | Who checks the work? (fresh-context subagents, no author bias) | advisory |
| **Enforcement** | `.claude/hooks/` + `.githooks/` | What can never happen? | **blocking** |

The common failure mode this prevents: writing enforcement-layer intent
("never commit a regression") into the facts layer, where it is a polite
suggestion an agent can talk itself past.

### The enforcement loop in practice

- Every `src/` edit → PostToolUse hook runs the **invariant suite** (absolute,
  100% required). A failure is fed straight back to the editing agent as an
  error it must fix — no human in the loop.
- Every commit → pre-commit hook runs the **fast suite** against
  `.eval-baseline.json`. A score below baseline blocks the commit. The
  baseline moves only by explicit decision, recorded in an ADR.
- Every session end → the session's prompts are dumped to `prompts/raw/`,
  so the AI-collaboration record builds itself.

Every gate run appends a `history.jsonl` line; a full per-case report is
written only on request, `--suite all`, or a red run (groundwork GW-008).

Enforcement is deliberately **repo-side, never plugin-side**: a plugin can be
disabled silently; a hook versioned with the code cannot.

### The execution layer in practice

Four standing roles, all evidence-only (they may not fix anything). Claude Code
loads them as native agents; Codex loads role skills that spawn a no-history
subagent from the same canonical contract and only the bounded task packet:

- `cold-reviewer` — cold-reads new code without the author's reasoning; its
  deliverable is the three most likely *silent* failure inputs.
- `eval-adversary` — attacks the gaps in the eval set with real-world inputs;
  its findings become adversarial cases verbatim.
- `spec-drift` — audits gaps between what the repo says (invariants, contracts,
  ADRs, docs) and what the code does; flags decorative invariants first.
- `pr-reviewer` — falsification-only PR review inside the pr-loop delivery
  state machine; returns structured findings, never edits.

## Per-feature loop

```
failing eval case → implement (invariant hook watching) → cold review
→ findings become adversarial cases → eval gate green → commit
```

## Delivery loop (`/pr-loop` on Claude Code, `$pr-loop` on Codex)

For a full task that ends in a PR, the human is not the message broker between
an implementer session and a reviewer session. The orchestrator also prevents
the agents from repeatedly paying to rediscover the same repository context:

```
SPEC → IMPLEMENT → ANALYZE/PREFLIGHT → GATE → ADAPTIVE REVIEW
REVIEW ─ approve → EVIDENCE → HUMAN
REVIEW ─ findings → REPAIR → ANALYZE/PREFLIGHT → GATE → DELTA VERIFY
DELTA VERIFY ─ approve → EVIDENCE; open after call 2 → HUMAN
```

Agents own execution and adversarial review, the repo's gate owns objective
pass/fail, humans retain spec and merge authority. Before any reviewer call, a
stdlib analyzer turns the diff and an existing Graphify graph (when present)
into a compact impact/risk/context packet; Ponytail questions about new surface
must be resolved; a red gate returns directly to repair. The first reviewer
call is focused or full according to risk. If repair is needed, the second call
verifies only standing findings plus the repair diff. A third call requires an
explicit human choice (GW-009).

Before every subagent spawn, the orchestrator also chooses the least expensive
adequate model (GW-011): Sonnet for bounded Claude work, Luna for mechanical Codex
work, and Terra for ordinary Codex implementation/focused verification. High-risk
or full review, cross-cutting design, security/safety impact, ambiguity, and a
failed smaller-model attempt explicitly use Opus on Claude or Sol on Codex. An
initial task/repository risk screen protects the pre-diff implementer spawn. The
ledger records every attempt and substitution; model routing does not change
isolation, gates, or call limits.

The orchestrator is outside that routing table (GW-012). It remains on Opus in
Claude Code or Sol in Codex because it owns global risk classification, state
transitions, budgets, and circuit breakers. An economy-model parent stops before
SPEC—or at any later model checkpoint—and asks the human to switch or restart.
Every check is recorded separately from subagent model routes.

The PR is an **evidence ledger**, not a communication bus: bounded role-tagged
comments, committed JSON findings, and a current evidence body. The metrics line
in `tasks/pr-loop-ledger.jsonl` records findings and repair outcomes plus review
calls/mode and actual reviewer tokens when exposed, so verification cost is
measured rather than guessed.

Three rules keep the loop convergent (GW-002, GW-009): a finding blocks only
if it breaks acceptance, the gate, or a published claim; blocking also needs
concrete evidence and confidence at least 0.80; and repair is batched before
one delta verification. Everything else becomes a **Debt** task in
`tasks/TODO.md`. Task blocks carry `Depends:` so independent tasks can run
as parallel pr-loop sessions on isolated `task/<id>` worktree branches. Codex
creates the worktree before spawning an implementer and gives the implementer
its absolute path as the mandatory working directory. The plugin's `ready.py`
lists what is unblocked. TODO.md stays small by design:
it holds only Queue and Debt; merged work becomes a one-liner in
`tasks/DONE.md`, and agents read single task blocks, never the whole file.

## Repo map

Skills and role contracts arrive through the dual-runtime **groundwork plugin**
(`plugin/` in the groundwork repo). `.claude-plugin/` registers Claude Code;
`.codex-plugin/` plus `.agents/plugins/marketplace.json` registers Codex. Repo-local
skills/agents hold only project-specific domain knowledge and override the plugin
on name collision. `plugin/assets/scaffold/` carries every file the initializer
may seed, because installed plugins execute from a cache without access to the
surrounding marketplace repository.

```
CLAUDE.md / AGENTS.md facts layer — working rules including the ## Gate section
.claude/settings.json  hooks registration + plugin wiring (groundwork + ponytail)
.agents/plugins/     Codex repo marketplace
.claude/hooks/       post-edit invariant runner · session prompt logger
.githooks/           pre-commit eval gate (installed via core.hooksPath)
tasks/               TODO.md (Queue / Debt — working set) + DONE.md (one-line merged index)
specs/               ONLY three kinds: invariants · output contracts · the PROJECT's ADRs
evals/run.py         stdlib-only runner — defines the case + adapter contract
plugin/skills/pr-loop/scripts/analyze.py  stdlib-only review planner; consumes diff + optional existing graph
evals/golden/        hand-verified cases (provenance recorded per case)
evals/adversarial/   inputs that broke, or are designed to break, the pipeline
evals/report/        history.jsonl (one line per run) + full reports only for requested/`all`/red runs and cited reports of record
prompts/             AI-collaboration record: auto-dumped raw/ + curated correction chains
src/<task>/          implementations — each exposes eval_adapter.py to the runner
docs/groundwork.md   this file — the groundwork process reference
```

## Namespace rule — whose decision is it?

- **The project's decisions** live in `specs/decisions/ADR-*.md`, numbered by
  the project from ADR-000. groundwork never ships an ADR into that
  namespace.
- **groundwork's own decisions** live in the groundwork repo under
  `docs/decisions/GW-*.md`. A project that adopts a groundwork mechanism
  references the GW number ("adopted pr-loop v2, rationale: groundwork
  GW-002") — it never copies the file.
- **Sync rule: mechanism ships, rationale is referenced.** What propagates to
  projects is skills, agents, and scaffold files; a `.groundwork-version`
  file records the upstream commit they came from.

## ADR format

Every ADR — project `specs/decisions/ADR-*.md` and groundwork's own
`docs/decisions/GW-*.md` alike — carries a mandatory 3-line header right
after the title/status line: **Ruling** (what is now true, ≤3 lines,
imperative), **Because** (the core reason, one line), **Enforced by** (case
ids / hook / code location, or `advisory — <where it binds>`). A `---` fold
line follows, then unbounded Context/Evidence/Alternatives/Consequences —
most readers need only the header; the fold is for the reader who needs the
story. Each repo also keeps `specs/decisions/INDEX.md`, one line per ADR
(`ADR-NNN — <ruling sentence> — enforced by <x>`) — the "what are the current
rules" digest. A repo with an eval harness adds an invariant-suite case
checking every ADR has the header and INDEX.md has exactly one line per ADR
file — see groundwork GW-006.

## If you are an agent entering a groundwork repo

1. Read the host's project instruction file (`CLAUDE.md` or `AGENTS.md`) in full.
2. Run its `## Gate` commands to see the current ground state.
3. Before changing behavior: write the failing case first, watch it fail.
4. Before claiming done: the gate is green.
5. When you hit a judgment call about what "correct" means — that is an ADR,
   not a code comment. Write it down in `specs/decisions/`.
