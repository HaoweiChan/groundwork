---
name: pr-loop
description: Orchestrated implement → verify → review → repair loop for one tasks/TODO.md task, ending in a PR that carries evidence, not chatter. Use when the user says /pr-loop <task-id>, /pr-loop next, "deliver T<N>", or asks to run a task through the full delivery loop.
---

# pr-loop — the delivery state machine

You are the **orchestrator**. You never write implementation code and never
review it yourself. You own state transitions, deterministic gates, and the
evidence ledger. The human's only two touchpoints are: invoking this skill,
and merging the PR.

```
SPEC → IMPLEMENT → GATE → REVIEW ─ findings → REPAIR → GATE → REVIEW …
                              └──── approve → EVIDENCE → HUMAN (merge)
```

Role separation is the verification architecture — do not collapse it:

| Role | Owns | May never |
|---|---|---|
| implementer (subagent, worktree) | implementation + tests | approve its own work |
| pr-reviewer (subagent, fresh context) | falsification, structured findings | edit code |
| eval suite | objective pass/fail | be skipped or mocked |
| orchestrator (you) | transitions, relay, ledger | implement or review |
| human | spec, disputes, merge | be needed mid-loop |

## States

### 1. SPEC
Housekeeping first: any TODO.md block with `status: pr` whose PR has since
merged is replaced by a one-liner in `tasks/DONE.md`
(`- <id> — <title> (<merge date>) — <refs>`).

Read the target task's block from `tasks/TODO.md` — locate it with grep and
read ONLY that block; never load the whole file into context. `/pr-loop next`
takes the first ready Queue task — list them with
`python3 "$CLAUDE_PLUGIN_ROOT"/skills/pr-loop/scripts/ready.py` (from the repo
root). A task with unmet `Depends:` is refused with the blocking ids, never
started early. If the spec lacks acceptance criteria you can gate on, STOP and
ask the human — that is a spec problem, not something to improvise past.

### 2. IMPLEMENT
Spawn an **implementer subagent with worktree isolation** on branch
`task/<id>`. Its prompt must contain: the full task block, the repo's
per-feature loop (failing eval case first), the debt rule below, and the
instruction to commit its work on the branch. It reports what it built and
which new eval cases it added.

**Debt rule (binds implementer and reviewer alike):** work discovered
mid-task that exceeds the spec — an adjacent bug, a refactor the code
"really needs", missing coverage elsewhere — is not done in this PR. Log it
as a task block under `## Debt` in `tasks/TODO.md` (with `Origin:`) and stay
on spec.

### 3. GATE (deterministic — you run it, never trust "I ran the tests")

**Branch freshness first — an orchestrator duty, every round.** The base is
the PR's target branch (`gh pr view --json baseRefName`; before the PR exists,
the branch the task was cut from) — never assume `main`. `git fetch origin`
and compare the task branch to `origin/<base>`. If the base advanced (parallel
pr-loop sessions merge while you run): `git merge origin/<base>` into the task
branch — merge, never rebase (a rebase needs a force-push). Textual conflicts
are implementer work: relay them as a repair item, never resolve them yourself
and never hand them to the reviewer. Then check for **semantic collisions**
git cannot see — the base added something in a namespace this branch also
adds (an ADR number, a task id, a case id, a TODO.md block): renumber or
reconcile on the branch. Only after the branch contains the base do you run
the gate — the gate must pass on the tree that will actually be merged, not on
a stale base. Record `Base: <base>@<sha>` in the PR body each time you sync.

On the (now current) task branch, run the commands in the repo CLAUDE.md's
**`## Gate`** section, in order, judged by the pass criteria stated there. No `## Gate`
section → STOP and ask the human to define one: a delivery loop without an
objective gate is two agents complimenting each other.
Fail → back to REPAIR with the raw output. Pass → first time through, push
the branch and `gh pr create`, body = the rolling evidence pack (template
under **PR body**, below) seeded with Round 0 = gate only, Decision: in
repair — never a placeholder like "evidence pack pending".
Then REVIEW.

### 4. REVIEW
Spawn the **pr-reviewer subagent** (fresh context, no author reasoning).
Round 1 reviews the full PR diff; **round 2+ reviews only the repair diff
plus the standing findings** — a fresh full-diff sweep every round finds new
findings forever and the loop never converges. It returns findings in this
schema, nothing else:

```json
{"id": "R1", "severity": "HIGH|MEDIUM|LOW",
 "claim": "what is wrong, one sentence",
 "evidence": "file:line + the concrete input/state that triggers it",
 "repro": "command or case that demonstrates it",
 "acceptance": "what passing looks like after the fix"}
```

**Scope boundary — what a finding may block.** A finding triggers REPAIR only
if it is HIGH/MEDIUM **and** at least one of:
- it violates the task's acceptance criteria,
- it turns the gate red,
- it makes a published number or claim dishonest — a metric that counts
  wrong, a committed artifact a reader would take as verified-correct, or
  repair-round history / superseded numbers / per-round narrative bled into
  a README, analysis report, or other document of record (that audit trail
  belongs only in `tasks/reviews/`, never in a final document).

Everything else — **regardless of severity** — goes to `## Debt` in
`tasks/TODO.md` with `Origin: PR #<n> <finding-id>` and the finding's
evidence carried verbatim. Severity says how bad; scope says whose PR.

Findings land in two places, never one — a full machine trace and a bounded
human summary. Never write full findings prose into a PR comment.

**Artifact (always, full detail).** Commit `tasks/reviews/pr<N>-r<K>.json` on
the branch: the reviewer's findings array in the schema above, unchanged,
plus the orchestrator's `route` tag per finding (`repair`|`debt`) and the
round's `result` (`APPROVED`|`REQUEST_CHANGES`). This is the reproducible
trace — every claim in the comment below must trace back to a line in it.

**Comment (bounded, exactly one, ≤40 lines):** `**pr-loop/reviewer — round
<N>**` — result, H/M/L counts, blocking findings as `id — one-line claim`
only (no evidence/repro prose), non-blocking ids listed flat, the gate line,
and the artifact path. Nothing else reaches the PR as reviewer chatter.

Then update the PR body (the rolling evidence pack — see **PR body**, below)
with this round's line.

- Any `repair` finding → REPAIR.
- None (only `debt`/LOW) → reviewer states APPROVED → EVIDENCE.

### 5. REPAIR
Relay the `repair` findings verbatim to the implementer (same subagent via
SendMessage if alive, else a fresh one on the same worktree branch). Hard
rule: **every confirmed repair finding becomes a failing case in the repo's
gate suite before it is fixed** — watch it fail, then fix. A finding the
implementer rejects gets a one-line written reason; the reviewer sees it next
round.

Resolutions land the same split way:

**Artifact (always, full detail).** Commit
`tasks/reviews/pr<N>-r<K>-resolution.json` — one entry per finding id:
`fixed` (+ the eval/case id that now covers it), `rejected` (+ the one-line
reason), or `debt` (+ the T-id it became).

**Comment (bounded, exactly one, ≤40 lines):** `**pr-loop/implementer —
round <N>**` — resolved/rejected/debt-logged counts, up to 5 bullets of
material changes, one verification line (the command that shows the fix),
and the resolution artifact path.

Then → GATE, which updates the PR body with the round's result line.

**Circuit breaker:** after 3 review rounds without approval, or any
implementer/reviewer deadlock on a finding, stop — do not loop forever. Post
one escalation comment (`**pr-loop/orchestrator — circuit breaker**`, ≤40
lines, one compact block): breaker state · open H/M/L counts · the one
blocker finding (id + one line + the key number — the single finding
actually stalling merge, not a list) · structural findings if any (one line
each) · Options A (one more bounded round) / B (merge with the finding
logged as named debt) · a recommendation. The human must be able to decide
from this block alone, with no other comment or artifact read required —
relay the same block to the human directly, don't just post and wait.

### 6. EVIDENCE
Reviewer approved. Do one last freshness sync (the base may have moved during
the final round) — if it brings changes, GATE again before finalizing; a PR
handed to the human must be `mergeable` against its current base. Then finalize
the rolling PR body: set **Decision** to `awaiting human`, drop resolved findings from "Important failures
discovered" (it lists current material findings, not history), confirm the
gate line reflects the last green run, and fill in **Verification** (the
one command a human can run to see it work) and **Debt logged** (T-ids
created this task, or `none`) — both were live-updatable earlier but must
be correct and present by this state.

Append one line to `tasks/pr-loop-ledger.jsonl` (the workflow's own
eval — commit it with the branch):

```json
{"task":"T10","date":"YYYY-MM-DD","rounds":2,"findings":{"HIGH":1,"MEDIUM":2,"LOW":1},"repaired":2,"rejected":1,"debt_logged":1,"gate_failures":1,"human_interventions":0}
```

Notify the human: task id, PR link, one-line summary. **You do not merge.**

## PR body — rolling evidence pack

The PR body is never a communication surface and never stale — the
orchestrator rewrites it after every gate run and every review, starting at
PR creation. Fixed template:

```markdown
## <task-id> — <goal, one line>
<goal, second line — what "done" means>

### Rounds
Round 1: 2 HIGH / 1 MEDIUM / 0 LOW → repaired 3, rejected 0, debt 0
Round 2: 1 HIGH / 4 MEDIUM / 3 LOW → repaired 7, rejected 0, debt 1

### Important failures discovered
1. <one line, only material ones — in-scope HIGH/MEDIUM findings>
2. <one line>

**Gate**: pass — 2026-08-20
**Base**: <base>@<sha> — synced round <N>, mergeable
**Full trace**: tasks/reviews/pr<N>-r*.json
**Verification**: <the one command a human can run to see it work>
**Debt logged**: <T-ids created this task, or none>
**Decision**: in repair
```

Rounds accumulate (append, never rewrite); "Important failures discovered"
is the *current* set of material findings, not a log — a repaired finding
drops off the list rather than staying struck through. **Decision** is one
of `in repair` (loop active, more rounds possible), `awaiting human`
(reviewer approved, nothing left to automate), or `merged` (terminal).
Nothing else lives in the body: no per-round narrative, no repair-history
prose, no superseded numbers. That is the audit trail, and it lives in
`tasks/reviews/`, never in the document a human reads to decide.

## PR comment identity

Every PR comment is posted by the same `gh` account, so the first line of
each comment MUST declare the role — this is how the human tracks who said
what:

```
**pr-loop/reviewer — round <N>**      bounded summary, ≤40 lines → tasks/reviews/pr<N>-r<K>.json
**pr-loop/implementer — round <N>**   bounded resolution, ≤40 lines → tasks/reviews/pr<N>-r<K>-resolution.json
**pr-loop/orchestrator — circuit breaker**   escalation block only — every other orchestrator update is a PR body edit, not a comment
```

One comment per role per round, always tagged, always ≤40 lines. The PR body
carries the rolling evidence pack; comments never repeat what the body or the
artifacts already say.

## tasks/TODO.md format

TODO.md is the WORKING SET only — two sections, one shared id sequence
(`T<N>` by convention; any letter-prefix id like `M8` works — legacy
milestone ids keep their names):

- `## Queue` — runnable work, in priority order.
- `## Debt` — findings and overflow logged by pr-loop runs; same block format
  plus `Origin:`. Promoting debt = moving the block into Queue.

Merged work leaves TODO.md entirely: the block is replaced by a one-liner in
**`tasks/DONE.md`** (`- <id> — <title> (<merge date>) — <refs>`). The
narrative already lives in the ADRs/PR and the ledger; DONE.md is an index,
not an archive. ready.py reads DONE.md ids when resolving `Depends:`.

```markdown
### T10 — <title>            [status: todo|in-progress|pr|done]
Depends: T3, T7        (optional — task ids that must be done first)
Origin: PR #12 R12     (debt blocks only — which PR/finding produced it)
Spec: what and why, 2-5 lines.
Acceptance: gateable criteria — eval cases, invariants, or a runnable check.
Out of scope: (optional)
```

ready.py lists every Queue task whose deps are all done — open one pr-loop
session per ready task; the `task/<id>` worktree branches keep parallel runs
isolated. Update the `status` field at each transition (in-progress at
IMPLEMENT, pr at EVIDENCE; after the human merges, the next pr-loop run's
housekeeping moves the block to DONE.md).
