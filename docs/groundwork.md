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
| **Facts** | `CLAUDE.md` | What is invariantly true here? (structure, commands, hard rules) | advisory |
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

Enforcement is deliberately **repo-side, never plugin-side**: a plugin can be
disabled silently; a hook versioned with the code cannot.

### The execution layer in practice

Four standing subagents, all evidence-only (they may not fix anything):

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

## Delivery loop (/pr-loop)

For a full task that ends in a PR, the human is not the message broker between
an implementer session and a reviewer session — an orchestrator session owns
the state machine:

```
SPEC → IMPLEMENT → GATE → REVIEW ─ findings → REPAIR → GATE → REVIEW …
(human)  (subagent,  (repo's  (pr-reviewer,        └─ approve → EVIDENCE → HUMAN
          worktree)   gate)    fresh context)                    (pack)     (merge)
```

Agents own execution and adversarial review, the repo's gate owns objective
pass/fail, humans retain spec and merge authority. The PR is an **evidence
ledger**, not a communication bus: one role-tagged structured findings comment
per review round, a final evidence pack, and a metrics line per task in
`tasks/pr-loop-ledger.jsonl` — so the workflow itself is evaluated
(review rounds, repaired vs rejected vs debt-logged findings, human
interventions).

Two rules keep the loop convergent (GW-002): a finding blocks a round only
if it breaks the task's acceptance criteria, the gate, or the honesty of a
published claim — everything else becomes a **Debt** task in `tasks/TODO.md`
rather than round fuel; and only round 1 sweeps the full diff — later rounds
review the repair. Task blocks carry `Depends:` so independent tasks can run
as parallel pr-loop sessions on isolated `task/<id>` worktree branches — the
plugin's `ready.py` lists what is unblocked. TODO.md stays small by design:
it holds only Queue and Debt; merged work becomes a one-liner in
`tasks/DONE.md`, and agents read single task blocks, never the whole file.

## Repo map

Skills and agents arrive through the **groundwork plugin** (`plugin/` in the
groundwork repo, self-hosted marketplace); repo-local `.claude/skills/` and
`.claude/agents/` hold only project-specific domain knowledge, which overrides
the plugin on name collision.

```
CLAUDE.md            facts layer — working rules incl. the ## Gate section (AGENTS.md symlinks here)
.claude/settings.json  hooks registration + plugin wiring (groundwork + ponytail)
.claude/hooks/       post-edit invariant runner · session prompt logger
.githooks/           pre-commit eval gate (installed via core.hooksPath)
tasks/               TODO.md (Queue / Debt — working set) + DONE.md (one-line merged index)
specs/               ONLY three kinds: invariants · output contracts · the PROJECT's ADRs
evals/run.py         stdlib-only runner — defines the case + adapter contract
evals/golden/        hand-verified cases (provenance recorded per case)
evals/adversarial/   inputs that broke, or are designed to break, the pipeline
evals/report/        every run's scored output, committed — the progress narrative
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

## If you are an agent entering a groundwork repo

1. Read `CLAUDE.md` in full — it is short on purpose.
2. Run the gate (see CLAUDE.md `## Gate`) to see the current ground state.
3. Before changing behavior: write the failing case first, watch it fail.
4. Before claiming done: the gate is green.
5. When you hit a judgment call about what "correct" means — that is an ADR,
   not a code comment. Write it down in `specs/decisions/`.
