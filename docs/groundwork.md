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
an implementer session and a reviewer session. pr-loop is a closed control
loop in the loop-engineering sense — sensors (the repo's gate and the task's
live probe), an actuator (the implementer), and an independent controller (the
verifier) — with no human inside it (GW-017). It iterates over tasks; inside
one task it makes at most two model calls:

```
SPEC → IMPLEMENT → ANALYZE/PREFLIGHT → GATE → PROBE → VERIFY (call 1)
VERIFY ─ met → EVIDENCE → HUMAN
VERIFY ─ blocking findings → REPAIR (once) → GATE → PROBE → RE-VERIFY (call 2)
RE-VERIFY ─ met → EVIDENCE → HUMAN;  not met → EVIDENCE (Decision: not met) → HUMAN
```

Agents own execution and verification, the repo's gate and the task's probe own
objective pass/fail, humans retain spec and merge authority. Before the model
call, a stdlib analyzer turns the diff and an existing Graphify graph (when
present) into a compact impact/risk/context packet; Ponytail questions about
new surface must be resolved; a red gate or a failed probe returns to the
implementer without spending a call. The verifier answers three questions —
acceptance met, drift from the task, wrong output on realistic input — and a
finding blocks only with a reproduction. Prose, naming, and documentation are
never findings. If anything blocks, one batched repair, then one delta
verification. What is still open after that goes to the human as
`Decision: not met`; there is no third call and nothing that asks the human to keep going.

Before every subagent spawn, the orchestrator chooses the least expensive
adequate capability level (GW-011, GW-014): Sonnet-level for bounded Claude
work, Luna-level for mechanical Codex work, Terra-level for ordinary Codex
implementation and delta verification. Call 1 verification, high-risk or full
analysis, security/safety impact, ambiguity, and a failed smaller-model attempt
require Opus-level or stronger on Claude and Sol-level or stronger on Codex. An
initial task/repository risk screen protects the pre-diff implementer spawn.
The ledger records every attempt and substitution; routing does not change
isolation, gates, or the call limit.

The orchestrator is outside that routing table (GW-012, GW-014). It stays at
Opus-level or stronger in Claude Code and Sol-level or stronger in Codex because
it owns risk classification, state transitions, and the budget. Newer stronger
tiers qualify automatically. A lower-tier parent stops before SPEC — or at any
later checkpoint — and asks the human to switch or restart. Every check is
recorded separately from subagent model routes.

The PR is an **evidence ledger**, not a communication bus: the six-section body
that `.github/pr_check.py` enforces (Why, What changed, Verification, Problems
found, Follow-ups, Reviewer notes), one committed findings JSON per PR, and one
verifier comment. `tasks/pr-loop-ledger.jsonl` records findings, repair
outcomes, calls spent, probe run ids and cost, and actual reviewer tokens when
exposed.

Task state lives in Backlog.md, one file per task. SPEC reads
`backlog task list --ready --plain` and one `backlog task view <id> --plain`,
never the board. A task is eligible only if its acceptance can be checked inside
the PR and it declares a `Probe:` line (a live command with a budget, or `none`
with a structural reason). A task whose probe must run on a post-merge deploy
stays open under the same id until that probe is green — the same problem never
reopens under a new number. Debt is one `backlog task create --draft` line that
names a `case <id>` or `run <id>`; drafts are invisible to the working set until
a human promotes one. Codex creates the task worktree before spawning an
implementer and gives it the absolute path as the mandatory working directory.

## Repo map

Skills and role contracts arrive through the dual-runtime **groundwork plugin**
(`plugin/` in the groundwork repo). `.claude-plugin/` registers Claude Code;
`.codex-plugin/` plus `.agents/plugins/marketplace.json` registers Codex. Repo-local
skills/agents hold only project-specific domain knowledge and override the plugin
on name collision. `plugin/assets/scaffold/` carries every file the initializer
may seed, because installed plugins execute from a cache without access to the
surrounding marketplace repository.

The Groundwork source repository has one additional boundary (GW-013): root
`evals/`, `src/`, and `specs/` are seed material for an adopting project, not a
place to verify the plugin itself. Groundwork's own stdlib-only contracts live in
`plugin/tests/`; its source-repo hooks run that suite. The bundled scaffold keeps
the eval hooks described above for descendant projects.

```
CLAUDE.md / AGENTS.md facts layer — working rules including the ## Gate section
.claude/settings.json  hooks registration + plugin wiring (groundwork + ponytail)
.agents/plugins/     Codex repo marketplace
.claude/hooks/       post-edit invariant runner · session prompt logger
.githooks/           pre-commit eval gate (installed via core.hooksPath)
backlog/             Backlog.md task store (one file per task; drafts/ hold debt; completed/ holds merged work)
specs/               ONLY three kinds: invariants · output contracts · the PROJECT's ADRs
evals/run.py         stdlib-only runner — defines the case + adapter contract
plugin/skills/pr-loop/scripts/analyze.py  stdlib-only review planner; consumes diff + optional existing graph
plugin/tests/        Groundwork's own plugin contracts and regressions
evals/golden/        project seed for hand-verified cases (empty in this source repo)
evals/adversarial/   project seed for breaking inputs (empty in this source repo)
evals/report/        project seed for run history/reports (empty in this source repo)
prompts/             AI-collaboration record: auto-dumped raw/ + curated correction chains
src/<task>/          project implementation seed (empty in this source repo)
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
