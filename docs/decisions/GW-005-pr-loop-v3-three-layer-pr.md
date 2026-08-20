# GW-005 — pr-loop PR is a bounded interface, not a shared transport
Status: accepted · 2026-08-20 · Amends: GW-001, GW-002

**Ruling**: The PR body is a rolling evidence pack, always current;
reviewer/implementer comments are ≤40-line bounded summaries, one per role
per round; full findings/dispositions live as committed JSON in `tasks/reviews/`, never as comment prose or narrative in a document of record.
**Because**: the PR was serving as agent transport, debug log, review
database, and human interface at once — the surface a human reads most was
also the one carrying the most agent noise and the least-current state.
**Enforced by**: `plugin/skills/pr-loop/SKILL.md` — REVIEW, REPAIR, EVIDENCE,
"PR body — rolling evidence pack", and "PR comment identity" sections.

---

## Context

The first two real pr-loop runs (browser-agent PR #12, sec-10k PR #12)
produced unreadable PRs. Symptoms observed directly in those transcripts:

- Reviewer comments carried all 11 findings with full evidence/repro prose
  each round — a human had to read the same detail 3-4 times as rounds
  repeated.
- Implementer reply comments carried full dispositions with reproduction
  detail for every finding, doubling the noise per round.
- The PR body still read "evidence pack pending" at round 4 — the
  single most-read surface (what a human opens first) was also the
  stalest, because it was only ever written once, at the end.
- Repair-round history and superseded numbers were being prepended into
  final documents (analysis reports) — the audit trail bled into the
  technical document of record, so a reader of the *report* couldn't tell
  current findings from resolved ones without cross-referencing PR history.

## Hypothesis

GitHub's PR (body + comment thread) was being used as four different things
at once: the transport agents used to hand work to each other, the debug log
of what each agent tried, the database of review findings and their
resolutions, and the interface a human reads to make a merge decision. Each
of those four wants a different shape — transport wants completeness, a
database wants structure, a human interface wants boundedness — and
collapsing them into one growing comment thread optimizes for none of them.
GW-001/GW-002 already established "the PR is an evidence ledger, not a
communication bus," but didn't specify a size bound or a machine-readable
store, so agents kept writing ledger-shaped prose into an unbounded thread.

## The change

Three layers, three different mediums:

1. **Machine trace — full detail, git, not GitHub.** Full findings JSON
   (`tasks/reviews/pr<N>-r<K>.json`) and full dispositions JSON
   (`tasks/reviews/pr<N>-r<K>-resolution.json`) are committed on the branch.
   Same findings schema as before (id/severity/claim/evidence/repro/
   acceptance) — it just lives in a file, not a comment. 100% reproducible
   in git, and a human never has to open it.
2. **Human interface — bounded comments.** Exactly one comment per role per
   round, ≤40 lines: the reviewer states result + counts + blocking-finding
   one-liners + a pointer to the artifact; the implementer states
   resolved/rejected counts + ≤5 material-change bullets + a pointer to the
   artifact. A circuit-breaker escalation is one compact block a human can
   decide from without reading anything else.
3. **Rolling evidence pack — the PR body, kept current every round.** Task
   id + goal, one line per round's result, a live "important failures
   discovered" list (drops resolved findings, not a log), current gate
   state, and a decision line. Never a placeholder, never stale.

Audit-trail content (round history, superseded numbers, per-round narrative)
is banned from documents of record by the same scope-boundary mechanism
GW-002 already uses to route findings: a finding that a document reads that
way is in-scope as a dishonesty finding, blocking regardless of severity.

## Success criteria

- A human can determine PR state — what's blocking, what's resolved, is it
  mergeable — in under a minute, from the PR body and the round's comment
  alone.
- The merge decision requires no agent reasoning: circuit-breaker escalation
  and the rolling evidence pack are self-contained.
- Every reviewer claim remains reproducible from committed `tasks/reviews/`
  artifacts, not from memory of a comment thread.
- The full machine trace is preserved — nothing is lost, only relocated out
  of the human-read surface.

## Alternatives rejected

- **Keep one long comment thread, just ask agents to be more concise.**
  Tried implicitly by the existing "findings table" instruction — didn't
  hold under repeated real rounds; there's no enforcement, so comment size
  drifts back up with every fresh-context reviewer.
- **External review-tracking tool.** Rejected for the same reason GW-001
  rejected a custom orchestration harness — the repo already has a
  git-native place (`tasks/`) for exactly this kind of state; no need for
  new infrastructure.

## Consequences

- Two new committed files per review round (findings + resolution JSON);
  `tasks/reviews/` grows per-PR but is git history, not working-set state —
  same shape as `evals/report/`.
- The reviewer/implementer subagent prompts must be told to write these
  artifacts and keep comments under the line budget — a prompt change in
  the orchestrator's spawn instructions, not covered by this ADR's text.
- The "findings table" instruction and comment format described in GW-001/
  GW-002 are superseded for round-to-round communication; those ADRs'
  narrative is left as-is (historical record of the decision at the time),
  this ADR is the current ruling.
