# GW-008 — report history is one line per run; full dumps only when they earn it
Status: accepted · 2026-08-21

**Ruling**: Every eval run appends one line to `evals/report/history.jsonl` — the
progress narrative. A full per-case report is written only on `--report`,
`--suite all`, or a red run — and is a **report of record** only once cited by filename outside `evals/report/`.
**Because**: routine green gate runs (pre-commit, CI, pr-loop) only ever needed a
time series, but `run.py` dumped a full report on every run regardless.
**Enforced by**: `evals/run.py` report-write logic; descendant repos with an eval
harness add an invariant-suite case that every `evals/report/<ts>-*.json` cited
outside `evals/report/` resolves to a real file.

---

## Context

Measured in two descendant repos: browser-agent accumulated 159 reports / 4.8 MB
under `evals/report/`, sec-10k accumulated 188 reports / 18 MB — both entirely from
`run.py`'s unconditional per-run write. Of those, only 25–43% were ever cited
anywhere as a report of record; the rest were routine gate runs (the pre-commit
hook, CI, pr-loop's GATE step) whose only residual value is a time series — wall-
clock trend, case counts, pass/fail over time — which needs one line per run, not
a full-fidelity dump. Every one of those dumps also rode along in the PR diff.

## Decision

1. `evals/report/history.jsonl` gets one line per run, always (unless the caller
   passes `--no-report`, a hard off switch reserved for high-frequency, non-gate
   callers like the PostToolUse invariant hook — history there would be per-edit
   noise, not a progress narrative). Schema:
   `{"ts", "suite", "sha", "dirty", "passed", "total", "score", "wall_s",
   "cost_usd", "report"}` — `report` is the full report's basename, or `null`.
2. A full per-case report is written only when it can justify its cost: the
   caller explicitly asked (`--report`), the run swept everything (`--suite all`),
   or the run is red (a case failed, or score fell below baseline). A routine
   green gate run writes only the history line.
3. A full report becomes a **report of record** the moment a doc, spec, or task
   cites it by filename outside `evals/report/`. That citation must resolve —
   descendant repos with an eval harness gate this with an invariant-suite case
   that walks every `evals/report/<ts>-*.json` reference outside `evals/report/`
   and fails if the file it names doesn't exist.
4. An uncited full report may be pruned at any time; git history retains it, and
   the prune itself is recorded in the repo's own ADR (not groundwork's) so the
   deletion has a paper trail distinct from routine cleanup.
5. Bench, oracle, and instrument artifacts are not `run.py` reports — they are
   governed by whatever ADR introduces them, not this one.

## Alternatives rejected

- **Retention window (delete reports older than N days).** Rejected: time is the
  wrong axis — a report cited once on day one is a report of record forever,
  while a report never cited is noise from the moment it's written. Citation,
  not age, is what makes a report worth keeping.
- **Always write the full report, gzip it instead.** Rejected: still one write
  per gate run and still ships in every PR diff; compression shrinks the bytes
  without touching the actual complaint (159–188 files nobody reads).

## Consequences

- Routine gate runs (pre-commit, CI, pr-loop GATE) get materially smaller PR
  diffs — no full report unless the run is red.
- A red run still gets its full dump automatically, so failure investigation
  loses nothing.
- `--suite all` sweeps (used before milestones) always get a full report, since
  that's the case where "everything, in detail" is the point of the run.
- Descendant repos that already accumulated large `evals/report/` trees may want
  a one-time prune pass, each recorded per item 4 above — not part of this ADR.
- `.githooks/pre-commit` runs the gate itself, so its history line is written
  by the working tree it's about to commit — that line is necessarily
  unstaged and lands in the *following* commit, not the one it describes.
  Acceptable: the line is a time-series sample, not evidence for the commit
  it happens to precede.
