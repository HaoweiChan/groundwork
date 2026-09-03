---
name: pr-loop
description: Self-supervised delivery loop for one Backlog.md task — implement → gate → probe → independent verify → one repair → one delta verify → human merge, at most two model calls, ending in a six-section evidence PR. Use for /pr-loop or $pr-loop commands, requests to deliver a task id, or a full PR delivery loop.
---

# pr-loop — one closed loop per task (v4, GW-017)

You are the **orchestrator**. You never write implementation code and never
review it yourself. You own transitions, deterministic gates, the probe, the
two-call budget, and the evidence. The human invokes the loop and merges.

**Why it is called a loop.** In loop-engineering terms this is a closed control
loop: every task passes through the same sensors (gate + live probe) and the
same independent verifier before a human sees it, with no human inside the
loop. The loop iterates over *tasks*. Inside one task there are at most two
model calls and never a third — the measured cost of open-ended rounds (GW-017)
is why. Self-supervised means the executor never grades its own work; it does
not mean the pipeline argues with itself until it agrees.

### Orchestrator model floor

The orchestrator is never model-routed downward. The contract is capability-
based, never a product/version allowlist:

- Claude Code: `opus-level or stronger`.
- Codex: `sol-level or stronger`.

A newer or stronger tier always satisfies the floor; for example, a tier above
Opus is valid. Do not require a particular model ID or version.

Model routing is subagent-only. Confirm the host capability tier before SPEC and
re-confirm it before every later state transition and every subagent spawn. If
the orchestrator changes to Sonnet-level, Terra-level, Luna-level, or another
lower tier, stop and ask the human to switch/restart at the required level; do
not begin or continue the state machine. The exact model ID may be unavailable:
use exposed tier metadata, the host session selector, or human confirmation as
capability evidence. Ask only when the tier itself is unknown,
never merely because the versioned ID is hidden.

The orchestrator MUST append every passed check to `orchestrator_checks` in the
evidence ledger with `checkpoint`, `requested`, `effective`, `evidence`,
`verified_at`, and `outcome`. `effective` is `null` when the exact model ID is
hidden. Keep this trace separate from subagent `model_routes`.

```
SPEC → IMPLEMENT → ANALYZE/PREFLIGHT → GATE → PROBE → VERIFY (call 1)
VERIFY ─ met → EVIDENCE → HUMAN
VERIFY ─ blocking findings → REPAIR (once) → GATE → PROBE → RE-VERIFY (call 2)
RE-VERIFY ─ met → EVIDENCE → HUMAN
RE-VERIFY ─ not met → EVIDENCE (Decision: not met) → HUMAN
```

| Role | Owns | May never |
|---|---|---|
| implementer (subagent, worktree, weaker model allowed) | red-first cases, implementation, probe run | grade its own work |
| pr-reviewer (subagent, fresh context, stronger model) | one acceptance/drift/wrong-output verification + one delta verification | edit code, review prose |
| analyzer + gate + probe | deterministic context/risk, objective pass/fail, live truth | be skipped or mocked |
| orchestrator | transitions, freshness, routing, budget, evidence | implement or review |
| human | task spec, merge, `not met` decisions | be needed inside the loop |

Budget: **at most two model calls** per task — one verification and one delta
re-verification. Deterministic analyzer, gate, and probe runs do not count.
There is never a third call; what is still open after call 2 goes to the human
as `Decision: not met`, not to another round.

### Model routing — decide before every spawn

Make an explicit model-routing decision before every subagent spawn. Choose the
least expensive model that can reliably satisfy the bounded role; model size is
a cost control, never a substitute for the gate or actor/verifier separation.

| Work | Claude Code | Codex |
|---|---|---|
| Mechanical, low-risk, tightly specified | `sonnet-level` | `luna-level` |
| Ordinary implementation, delta verification | `sonnet-level` | `terra-level` |
| Verification (call 1), high-risk/full analysis, security/safety, spec ambiguity, or a failed smaller-model attempt | `opus-level or stronger` | `sol-level or stronger` |

Resolve each level to a currently supported host model when spawning; model IDs
and versions are runtime data, not policy. Never use `inherit` or an unspecified
host default as a synonym for the required level. Any fallback must meet or exceed the requested capability level; choose the
least expensive known adequate substitute and record it. Before a high-risk subagent begins,
confirm the effective capability tier for every high-capability route using
host metadata, the resolved host mapping, organization policy, or human
confirmation. If that tier is unknown,
stop for human routing; a hidden exact model ID alone is not a reason to stop. All Codex implementer and reviewer spawns use
`fork_turns: "none"`; routing never relaxes worktree isolation, bounded
context, the call budget, or the independent-verification contract.

## 1. SPEC

Task state lives in Backlog.md. Read one task, never the board:

```bash
backlog task list --ready --plain --sort priority --limit 5   # /pr-loop next takes the first
backlog task view <id> --plain                                # the task, verbatim
backlog task edit <id> -s "In Progress"
```

Read nothing else from the task store. A task is **eligible** only if its
description carries a runnable acceptance and a probe line:

```
Probe: <command that exercises the deployed or live behavior> · budget $<x> · reps <n>
Probe: none — <structural reason, e.g. pure library change with no live surface>
```

Acceptance criteria that cannot be checked inside this PR (a deployment that
does not exist yet, a paid run nobody authorized) make the task
**not eligible**: stop, tell the human what would make it checkable, and do not
improvise. Exploratory work is not a pr-loop task; run it in a plain session and
create the task afterwards.

`/pr-loop analyze` or `$pr-loop analyze` is the read-only entry point: run the
analyzer in section 3 against the requested base/head, print its packet, stop.

## 2. IMPLEMENT

Before selecting the implementer model, run an initial risk screen from the
task block and acceptance criteria, referenced paths,
repository contracts/instructions, dependency manifests, and an
existing Graphify graph when present. Treat authentication/authorization, security/privacy, payments,
destructive operations, migrations, public schemas/APIs, concurrency, shared
infrastructure, cross-cutting changes, and unclear acceptance as high risk.
Unknown initial risk uses the explicit high-capability level. Record the
evidence and classification in the first model route entry.

Before spawning, create or attach a real task worktree from the repository root,
at an explicit absolute path outside the orchestrator checkout:

```bash
worktree_parent="$(mktemp -d "${TMPDIR:-/tmp}/groundwork-<task>.XXXXXX")"
git worktree add -b "task/<id>" "$worktree_parent/worktree" "origin/<base>"
```

For a resumed branch, omit `-b`. Verify isolation by running
`git rev-parse --show-toplevel` once in the orchestrator checkout and once with
the task worktree as the working directory; the absolute paths must differ.

Spawn the implementer with `fork_turns: "none"`. Its initial task contains only
the task text, the repo's failing-case-first rule, the current base reference,
the debt rule below, and the absolute worktree path as its mandatory working
directory. It commits its work and reports new case ids with red-then-green
evidence and, when the task has a probe, the probe run ids and cost.

**Debt rule:** adjacent bugs, refactors, and missing coverage outside acceptance
are not implemented here. The implementer reports them; the orchestrator files
each one as a single draft line — see EVIDENCE.

## 3. ANALYZE / PONYTAIL PREFLIGHT (deterministic, zero model calls)

Run after implementation and again after any base sync that changes the diff.
Resolve `<pr-loop-skill-dir>` as the directory containing this `SKILL.md`:

```bash
python3 "<pr-loop-skill-dir>/scripts/analyze.py" \
  --base "origin/<base>" --head "<task-branch>" \
  --output "/tmp/pr-loop-<task>-analysis.json"
```

The analyzer reads the diff once and consumes `graphify-out/graph.json` when it
already exists; it never triggers Graphify extraction. Its analysis packet
carries changed surface, risk, Ponytail questions, impacted nodes, review mode
(`focused` or `full`), targets, and a bounded context-file allowlist. Resolve
every `preflight.question` before GATE (`reused` or `justified` with one
concrete reason) and enforce with `--resolutions ... --require-preflight`; exit
3 returns to the implementer without spending a model call.

## 4. GATE (deterministic, zero model calls)

**Freshness first.** Obtain the PR base with `gh pr view --json baseRefName`
(before the PR exists, the branch the task was cut from), fetch it, and merge
`origin/<base>` into the task branch — never rebase. Text conflicts return to
the implementer. If syncing changed the diff, rerun ANALYZE/PREFLIGHT.

Run the commands in the repo's `## Gate` section, in order, judged by its stated
thresholds. No Gate section means stop and ask the human. A red gate goes
straight back to the implementer with raw output; **never spend a model call on
a red gate**. On the first green run, push and open the PR with the six-section
body (see EVIDENCE) and `Decision: in progress`.

## 5. PROBE (deterministic, zero model calls, may cost money)

Run the task's `Probe:` line exactly as written, within its budget and reps,
against the build the PR produces. Record every run id and the cost on the PR's
`Live:` line. A probe that fails returns to the implementer like a red gate.

`Probe: none — <reason>` writes `Live: not run — <reason>` and is only valid
when SPEC accepted that reason. A task whose probe needs a deploy that only
happens after merge keeps its status at `PR` after merging until the probe has
run on the deployed build; it closes under the same task id, never as a new
task. That is the rule against reopening the same problem under a fresh number.

## 6. VERIFY (model call 1: independent verification)

Spawn the pr-reviewer with fresh context. In Claude Code use the registered
`pr-reviewer` agent. In Codex, spawn the reviewer with `fork_turns: "none"`;
its initial task invokes the bundled `$pr-reviewer` skill in `mode: review`.
Give it only: the task text, the green gate output, the probe run ids, the
analysis packet with preflight resolutions, and the branch diff. `focused`
covers acceptance and named targets over `review.context_files`; `full` covers
the analyzer's impacted surface, not the repository.

The verifier answers three questions and nothing else: is every acceptance
criterion met; did the implementation drift from the task; is there wrong
output on realistic input. Its response is one JSON object:

```json
{"result":"APPROVED|REQUEST_CHANGES","findings":[
  {"id":"R1","severity":"HIGH|MEDIUM|LOW",
   "claim":"one sentence","evidence":"file:line + triggering state",
   "repro":"command or case id that fails today","acceptance":"what passing looks like"}
]}
```

**A finding without a `repro` never blocks.** A prose, naming, documentation, or style finding never blocks and is
not filed; the verifier may mention them in
one PR comment line each. A finding blocks only when it has a repro and falls
under one of the three questions. Everything else with a repro becomes a draft
debt line (EVIDENCE); everything without one is discarded.

Commit the findings as `tasks/reviews/pr<N>.json` (one file per PR, rewritten
in place after call 2) and post one comment, at most 20 lines:
`**pr-loop/verifier**`, result, blocking ids with one-line claims, gate line,
probe run ids. No blocking findings → EVIDENCE.

## 7. REPAIR (once)

Hand every blocking finding to the implementer in one batch. Each becomes a
failing gate case first, then a fix; a rejection needs one sentence and
concrete evidence. Then rerun PREFLIGHT, GATE, and PROBE (when behavior
changed). A red gate or probe returns to the implementer without a model call.

## 8. RE-VERIFY (model call 2, delta only)

Same registered Claude agent, or a new Codex reviewer with `fork_turns: "none"`
in `mode: verify`. Give it only the standing findings, the resolutions, the new
case evidence, and the repair diff — not the whole PR. It returns:

```json
{"result":"APPROVED|OPEN","verifications":[
  {"id":"R1","status":"VERIFIED|OPEN","evidence":"why the resolution meets or misses acceptance"}
],"new_findings":[]}
```

`new_findings` may hold only a regression introduced by the repair diff, with a
repro. APPROVED → EVIDENCE. OPEN → EVIDENCE with `Decision: not met`; the human
decides. A reviewer invocation counts
toward the review-call budget even when it fails, returns invalid output, or is
retried at the high-capability level.

## 9. EVIDENCE

Do one last base freshness sync; if it changes the diff, rerun PREFLIGHT, GATE,
and PROBE. Require mergeability.

**PR body** is the six-section shape enforced by `.github/pr_check.py`; the
orchestrator fills it from the artifacts it already holds:

```markdown
## Why
<observed failure or goal, with run id / case id / issue>
<details><summary>Task (verbatim): <id> — <title></summary>

> <`backlog task view <id> --plain` from `## Description` down, every line prefixed with `> `>
</details>

## What changed
- <behavior, mechanism>
Not changed: <scope left alone, or none>

## Verification
Gate: <suite> N/N · <suite> N/N · <sha>
Red-first: <case-id> watched red at <sha>, green at <sha>
Live: run <id> ×<n> on build <sha> · $<cost>   |   Live: not run — <reason>
Not verified: <what nobody checked, or none>

## Problems found
- <claim> → <evidence> → fixed (case <id>) | rejected (<reason>) | debt (task <id>)

## Follow-ups
- <one line per draft, each naming case <id> or run <id>>

## Reviewer notes
Start here: <riskiest hunk>
Reproduce: <one command>
```

The body is current state, not history. `Task (verbatim)` is pasted once at PR
creation and never edited (GW-016) — as a blockquote, never a code fence (a
fence shows raw markdown and scrolls sideways) and never raw (its `## ` headings
would become PR sections; `pr_check.py` rejects them); `Problems found` lists what this PR met and
how it was settled; resolved findings do not linger as rounds.

**Debt.** Every non-blocking finding with a repro, and every adjacent issue the
implementer reported, becomes one draft — one line, no Spec, no Acceptance:

```bash
backlog task create "<claim in one sentence>" --draft -l debt \
  --ref "PR #<n> R<k>" --ac "case <id> green"      # or --ac "run <id> passes"
```

A draft without a `case <id>` or `run <id>` is not debt and is not created.
Drafts never appear in `backlog task list`; a human promotes one when it is
worth doing and writes the spec then.

**Ledger.** Append one line to `tasks/pr-loop-ledger.jsonl`:

```json
{"task":"TASK-10","date":"YYYY-MM-DD","orchestrator_checks":[{"checkpoint":"SPEC","requested":"sol-level+","effective":null,"evidence":"host session selector","verified_at":"YYYY-MM-DDTHH:MM:SSZ","outcome":"confirmed"},{"checkpoint":"VERIFY","requested":"sol-level+","effective":null,"evidence":"unchanged host session selector","verified_at":"YYYY-MM-DDTHH:MM:SSZ","outcome":"confirmed"}],"review_calls":2,"review_mode":"focused","model_routes":[{"role":"implementer","attempt":1,"requested":"terra-level","effective":null,"evidence":"host mapping confirmed terra-level","risk":"ordinary","reason":"bounded task; no initial high-risk signals","outcome":"completed"},{"role":"verifier","attempt":1,"requested":"sol-level","effective":null,"evidence":"host mapping confirmed sol-level","risk":"medium/focused","reason":"call 1 always runs at the high-capability level","outcome":"completed"}],"review_input_tokens":null,"review_output_tokens":null,"probe":{"runs":["7b2e91aa"],"cost_usd":0.01},"findings":{"HIGH":0,"MEDIUM":1,"LOW":0},"repaired":1,"rejected":0,"debt_logged":1,"gate_failures":0,"decision":"met"}
```

Record actual token counts only when the runtime exposes them; otherwise
`null`. Record every spawn attempt in `model_routes` — `role`, `attempt`,
`requested`, `effective`, `evidence`, `risk`, `reason`, `outcome` — including
failed or substituted attempts. `review_calls` is 1 or 2, never more.

Set the task status: `backlog task edit <id> -s PR`. After the human merges and
any post-merge probe has run, the human or the next session sets `Done`;
`backlog cleanup` moves it out of the working set. Notify the human with the
task id, the PR link, one line, calls spent, and the decision. You do not merge.
