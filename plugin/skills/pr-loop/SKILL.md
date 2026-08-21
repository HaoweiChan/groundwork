---
name: pr-loop
description: Cost-aware implement → analyze → gate → review → repair delivery loop for one tasks/TODO.md task, ending in an evidence-backed PR. Use for /pr-loop or $pr-loop commands, requests to deliver a task id, or a full PR delivery loop.
---

# pr-loop — cost-aware delivery state machine

You are the **orchestrator**. You never write implementation code and never
review it yourself. You own transitions, deterministic gates, the review-call
budget, and the evidence ledger. The human invokes the loop and merges the PR.

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
use exposed tier metadata, the host session selector, or
human confirmation as capability evidence. Ask only when the tier itself is
unknown, never merely because the versioned ID is hidden. No task size, risk
class, budget pressure, or retry permits an economy orchestrator.

The orchestrator MUST append every passed check to `orchestrator_checks` in the
evidence ledger with `checkpoint`, `requested`, `effective`, `evidence`,
`verified_at`, and `outcome`. `effective` is `null` when the exact model ID is
hidden. Keep this trace separate from subagent `model_routes`; never collapse it
to the initially selected model.

```
SPEC → IMPLEMENT → ANALYZE/PREFLIGHT → GATE → REVIEW
REVIEW ─ approve → EVIDENCE → HUMAN
REVIEW ─ findings → REPAIR → ANALYZE/PREFLIGHT → GATE → VERIFY
VERIFY ─ approve → EVIDENCE
VERIFY ─ open after call 2 → HUMAN
```

| Role | Owns | May never |
|---|---|---|
| implementer (subagent, worktree) | implementation, cases, preflight resolutions | approve its own work |
| pr-reviewer (subagent, fresh context) | one falsification review + bounded delta verification | edit code |
| analyzer + eval suite | deterministic context/risk + objective pass/fail | be skipped or mocked |
| orchestrator | transitions, freshness, routing, budget, ledger | implement or review |
| human | spec, disputes, merge, optional third review call | be needed inside the default two-call loop |

Default model-review budget: **2 calls total** — one adaptive review and one
delta verification. A third call requires explicit human choice at the circuit
breaker. Deterministic analyzer and gate runs do not count as model-review calls.

### Model routing — decide before every spawn

Make an explicit model-routing decision before every subagent spawn. Choose the
least expensive model that can reliably satisfy the bounded role; model size is
a cost control, never a substitute for the gate or actor/reviewer separation.

| Work | Claude Code | Codex |
|---|---|---|
| Mechanical, low-risk, tightly specified | `sonnet-level` | `luna-level` |
| Ordinary implementation, focused review, delta verification | `sonnet-level` | `terra-level` |
| High-risk/full review, cross-cutting design, security/safety, spec ambiguity, or a failed smaller-model attempt | `opus-level or stronger` | `sol-level or stronger` |

Resolve each level to a currently supported host model when spawning; model IDs
and versions are runtime data, not policy. Use an explicit high-capability model
for every condition in the last row; never use `inherit` or an unspecified host
default as a synonym for the required level. Any fallback must meet or exceed the
requested capability level; choose the least expensive known adequate substitute
and record it. If no such tier is available or its capability is unknown, stop for
human routing. Before a high-risk subagent begins, confirm the effective
capability tier for every high-capability route using host metadata, the resolved
host mapping, organization policy, or human confirmation. If that tier is unknown,
stop for human routing; a hidden exact model ID alone is not a reason to stop.
All Codex implementer and reviewer spawns still use `fork_turns: "none"`; model
routing never relaxes worktree isolation, bounded context, call budgets, or the
independent-review contract.

## 1. SPEC

Housekeeping first: a TODO.md block with `status: pr` whose PR merged becomes a
one-liner in `tasks/DONE.md` (`- <id> — <title> (<merge date>) — <refs>`).

Read only the target block from `tasks/TODO.md`. `/pr-loop next` (Claude Code)
or `$pr-loop next` (Codex) uses the first ready Queue task. Resolve
`<pr-loop-skill-dir>` as the directory containing this `SKILL.md`, then run:

```bash
python3 "<pr-loop-skill-dir>/scripts/ready.py"
```

Refuse unmet `Depends:`. If acceptance criteria are not gateable, stop and ask
the human; do not improvise a spec.

`/pr-loop analyze` or `$pr-loop analyze` is the read-only entry point: run the
analyzer in section 3 against the requested base/head, print its compact packet,
and stop. It does not spawn an implementer or reviewer.

## 2. IMPLEMENT

Before selecting the implementer model, run an initial risk screen from the task
block and acceptance criteria, referenced paths, repository contracts/instructions,
dependency manifests, and an existing Graphify graph when present. Do not wait for
the implementation diff. Treat authentication/authorization, security/privacy,
payments, destructive operations, migrations, public schemas/APIs, concurrency,
shared infrastructure, cross-cutting changes, and unclear acceptance as high risk.
Unknown initial risk uses the explicit high-capability level. Record the evidence
and classification in the first model route entry. The later deterministic
analyzer supersedes this preliminary classification for review and verification
routing.

Before spawning, create or attach a real task worktree from the repository root.
Use an explicit absolute path outside the orchestrator checkout:

```bash
worktree_parent="$(mktemp -d "${TMPDIR:-/tmp}/groundwork-<task>.XXXXXX")"
git worktree add -b "task/<id>" "$worktree_parent/worktree" "origin/<base>"
```

For a resumed branch, omit `-b` and name the existing branch. Verify isolation by
running `git rev-parse --show-toplevel` once in the orchestrator checkout and once
with the task worktree as the command working directory; the absolute paths must
differ. Stop if they do not.

Spawn the implementer with `fork_turns: "none"`; do not use the runtime default.
Its initial task contains only the full task block, the repo's
failing-case-first rule, the current base reference, this debt rule, and the
absolute worktree path as its mandatory working directory. The subagent may share
the host filesystem, but every command and edit must be scoped to that worktree.
It commits its work and reports new case ids plus fail-before/pass-after evidence.

**Debt rule:** adjacent bugs, refactors, and missing coverage outside acceptance
are not implemented here. Add a task under `## Debt` in `tasks/TODO.md` with an
`Origin:` and stay on spec.

## 3. ANALYZE / PONYTAIL PREFLIGHT (deterministic, zero model calls)

Run after implementation and again after any base sync that changes the task diff.
Use the `<pr-loop-skill-dir>` resolved in SPEC:

```bash
python3 "<pr-loop-skill-dir>/scripts/analyze.py" \
  --base "origin/<base>" --head "<task-branch>" \
  --output "/tmp/pr-loop-<task>-analysis.json"
```

The analyzer reads the diff once and consumes `graphify-out/graph.json` when it
already exists. It **never triggers Graphify extraction**; missing graph evidence
falls back honestly to changed files. Its packet contains changed surface, risk,
Ponytail questions, direct impacted nodes, review mode, targets, and a bounded
context-file allowlist.

Resolve every `preflight.question` before GATE. Ask the implementer to either
`reused` existing/stdlib code or `justified` the new file, dependency, or
abstraction with one concrete reason. Put the answers in a scratch JSON object
keyed by question id and then by every listed file, then enforce them:

```json
{"new-source-surface":{"files":{
  "src/new_module.py":{"outcome":"justified","reason":"first module for the accepted feature"}
}}}
```

```bash
python3 "<pr-loop-skill-dir>/scripts/analyze.py" \
  --base "origin/<base>" --head "<task-branch>" \
  --resolutions "/tmp/pr-loop-<task>-preflight.json" --require-preflight \
  --output "/tmp/pr-loop-<task>-analysis.json"
```

Exit 3 means at least one listed file lacks a resolution and returns directly to
the implementer without spending a reviewer call.
New surface may remain when justified; preflight is a decision gate, not a ban.

## 4. GATE (deterministic, zero model calls)

**Freshness first, every time.** Obtain the actual PR base with
`gh pr view --json baseRefName` (before the PR exists, use the branch the task was
cut from), fetch it, and merge `origin/<base>` into the task branch — never rebase.
Text conflicts return to the implementer. Check semantic collisions Git misses:
ADR numbers, task ids, case ids, and TODO blocks. If syncing changed the task diff,
rerun ANALYZE/PREFLIGHT before continuing.

Run the commands in the repo's `## Gate` section, in order, and judge them by its
stated thresholds. No Gate section means stop and ask the human. A red gate goes
straight to REPAIR with raw output; **never spend a reviewer call on a red gate**.

On the first green run, push and create the PR. Seed its rolling evidence body
with gate, base, analysis mode/risk/context count, preflight status, and Decision:
`in repair`. Never use an evidence placeholder.

## 5. REVIEW (model call 1: adaptive falsification)

Spawn the pr-reviewer with fresh context. In Claude Code use the registered
`pr-reviewer` agent. In Codex, spawn the reviewer with `fork_turns: "none"`; its
initial task explicitly invokes the bundled `$pr-reviewer` skill in
`mode: review`. Give it only:

- the task block and acceptance criteria;
- the green gate command/result;
- the full analysis packet and preflight resolutions;
- the branch diff.

The packet selects depth. `focused` checks acceptance, invariants, and named
targets over `review.context_files`. `full` audits the analyzer's impacted surface,
not the repository. The reviewer may read outside the allowlist only after naming
the missing file and why the packet is insufficient. Review order is acceptance →
invariants/gate evidence → changed behavior → design.

Reviewer response schema (one JSON object, no trailing status text):

```json
{"result":"APPROVED|REQUEST_CHANGES","findings":[
  {"id":"R1","severity":"HIGH|MEDIUM|LOW","confidence":0.91,
   "claim":"one sentence","evidence":"file:line + triggering state",
   "repro":"command or case","acceptance":"what passing looks like"}
]}
```

Route a finding to `repair` only when all are true: HIGH/MEDIUM, confidence
`>= 0.80`, concrete evidence/repro, and it violates task acceptance, turns the
gate red, or makes a published claim dishonest. Confidence `0.50–0.79` gets one
`clarify` trip in the same repair batch; after VERIFY it either has new evidence
or becomes debt. Lower confidence, LOW, and out-of-scope findings become Debt
regardless of severity. Confidence never replaces evidence or scope.

Commit `tasks/reviews/pr<N>-r1.json`: unchanged findings plus orchestrator `route`
(`repair|clarify|debt`) and result. Post one reviewer comment, at most 40 lines:
role header, result, H/M/L counts, blocking ids + one-line claims, clarify/debt ids,
gate line, analysis mode/risk, artifact path. Do not paste evidence prose.

No `repair` or `clarify` findings → EVIDENCE. Otherwise → REPAIR.

## 6. REPAIR (one batched implementer handoff)

Send all `repair` and `clarify` findings together. Every confirmed repair finding
first becomes a failing gate case; watch it fail, then fix it. A rejection gets
one sentence and concrete evidence. Clarifications answer the exact uncertainty;
they do not invite a refactor.

Commit `tasks/reviews/pr<N>-r1-resolution.json`, one entry per finding:
`fixed` + case id, `rejected` + reason/evidence, `clarified` + evidence, or `debt`
+ task id. Post one implementer comment (at most 40 lines): counts, up to five
material bullets, verification command, artifact path. Then rerun PREFLIGHT and
GATE. A red gate returns to this same repair step without calling the reviewer.

## 7. VERIFY (model call 2: delta only)

Use the same registered Claude agent or spawn a new Codex reviewer with
`fork_turns: "none"` whose task invokes the bundled `$pr-reviewer` skill in
`mode: verify`. Give it only standing finding records, their routes, resolutions,
newly added case evidence, and the repair diff. Do not include the original full
PR diff or ask whether the whole PR is good. It returns one JSON object:

```json
{"result":"APPROVED|OPEN","verifications":[
  {"id":"R1","status":"VERIFIED|OPEN|DEBT","confidence":0.96,
   "evidence":"why the resolution meets or misses acceptance"}
],"new_findings":[]}
```

For a `clarify` record, no new evidence means `DEBT`; `OPEN` requires new concrete
evidence and confidence at least 0.80. It may add a new finding only for a
regression introduced by the repair diff, tagged `repair-regression`. An in-scope
HIGH/MEDIUM `repair-regression` opens the circuit breaker when confidence is at
least 0.80; lower-confidence or out-of-scope regressions become debt. Commit
`tasks/reviews/pr<N>-r2-verification.json` and post one bounded reviewer round-2
comment. APPROVED with all records verified/debt → EVIDENCE.

Any open in-scope finding after call 2 opens the circuit breaker. Do not
automatically start a third reviewer or implementer round. Post and relay one
compact `**pr-loop/orchestrator — circuit breaker**` block: calls spent; the single
stalling finding and key evidence; option A one more bounded repair/verification
call; option B human disposition/debt; recommendation. The human must explicitly
choose A before model-review call 3.

## 8. EVIDENCE

Do one last base freshness sync. If it changes the diff, rerun PREFLIGHT, GATE,
and the analyzer. If risk or review targets materially expand, the circuit breaker
asks the human whether to spend a bounded verification call; do not silently hand
off stale review evidence. Require mergeability.

Finalize the PR body: Decision `awaiting human`, current material failures only,
last green gate/base, runnable verification, debt ids, and review cost. Append one
JSON line to `tasks/pr-loop-ledger.jsonl` and commit it:

```json
{"task":"T10","date":"YYYY-MM-DD","orchestrator_checks":[{"checkpoint":"SPEC","requested":"sol-level+","effective":null,"evidence":"host session selector","verified_at":"YYYY-MM-DDTHH:MM:SSZ","outcome":"confirmed"},{"checkpoint":"REVIEW","requested":"sol-level+","effective":null,"evidence":"unchanged host session selector","verified_at":"YYYY-MM-DDTHH:MM:SSZ","outcome":"confirmed"}],"review_calls":2,"review_mode":"focused","model_routes":[{"role":"implementer","attempt":1,"requested":"terra-level","effective":null,"evidence":"host mapping confirmed terra-level","risk":"ordinary","reason":"bounded task; no initial high-risk signals","outcome":"completed"},{"role":"review","attempt":1,"requested":"terra-level","effective":null,"evidence":"host mapping confirmed terra-level","risk":"medium/focused","reason":"analysis packet selected focused review","outcome":"completed"}],"review_input_tokens":null,"review_output_tokens":null,"findings":{"HIGH":1,"MEDIUM":2,"LOW":1},"repaired":2,"rejected":0,"debt_logged":1,"gate_failures":1,"human_interventions":0}
```

Record actual token counts only when the runtime exposes them; otherwise `null`,
never an estimate. Record every spawn attempt in `model_routes`, including failed
or substituted attempts; never collapse a retry into one final model value. Each
entry has `role`, `attempt`, `requested`, `effective` (or `null` when the runtime
does not expose it), `evidence` for the effective capability level, `risk`,
`reason`, and `outcome`. A reviewer invocation counts
toward the review-call budget even when it fails, returns invalid output, or is
retried at the high-capability level. Notify the human with task id, PR link,
one-line summary, and review calls spent. You do not merge.

## PR body — rolling evidence pack

```markdown
## <task-id> — <goal, one line>
<what done means, one line>

### Verification
- Gate: pass — <date>
- Base: <base>@<sha> — mergeable
- Analysis: <focused|full> — <risk> — <N> context files — graphify|changed-files
- Preflight: pass — <N> resolved questions
- Review: <calls used>/2 default calls — <current result>
- Models: <role/attempt/requested/effective/outcome summary from model_routes>
- Full trace: tasks/reviews/pr<N>-*.json
- Reproduce: <one command>
- Debt: <T-ids or none>

### Important failures discovered
1. <current in-scope material finding only, or none>

**Decision**: in repair | awaiting human | merged
```

The body is current state, not history. Resolved findings disappear. Full review
and repair history stays in committed artifacts. Every PR comment uses the shared
account's explicit role identity and is at most 40 lines:

```
**pr-loop/reviewer — round <N>**
**pr-loop/implementer — round <N>**
**pr-loop/orchestrator — circuit breaker**
```

## tasks/TODO.md format

TODO.md has only `## Queue` and `## Debt`, sharing one id sequence. Promotion
moves a Debt block to Queue. Merged blocks leave TODO.md for DONE.md.

```markdown
### T10 — <title>            [status: todo|in-progress|pr|done]
Depends: T3, T7        (optional)
Origin: PR #12 R12     (debt only)
Spec: what and why, 2–5 lines.
Acceptance: gateable criteria.
Out of scope: (optional)
```

Update status at transitions: `in-progress` at IMPLEMENT, `pr` at EVIDENCE.
