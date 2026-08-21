# 001 — pr-loop change-analysis contract

The deterministic pre-review analyzer accepts a unified git diff and optional
Graphify graph. It returns a non-empty JSON object with these stable top-level
keys: `version`, `change`, `risk`, `preflight`, `impact`, and `review`.

For every non-empty diff:

- `change.files` lists each changed path once and reports added/deleted line totals.
- `preflight.questions` identifies new source surface and dependency-manifest
  changes for Ponytail resolution before review. With `--require-preflight`,
  the command exits 3 until each question has a non-empty `reused` or `justified`
  resolution for every listed file in the supplied JSON file.
- `impact.source` is `graphify` only when graph evidence was actually loaded;
  otherwise it is `changed-files`. Graph neighbors are bounded and deterministic.
- `risk.level` is `low`, `medium`, or `high`, with machine-readable reasons.
- `review.mode` is `focused` unless a high-risk reason requires `full` review.
- `review.context_files` is a deduplicated, bounded allowlist containing every
  changed file before any graph-derived context.

The analyzer is stdlib-only, makes no network or model calls, and never invents a
Graphify impact when no graph is available.

The reviewer and orchestrator share one confidence routing boundary: findings at
or above 0.80 may route to repair when evidence and scope also pass; findings from
0.50 through 0.79 route to one clarification; lower-confidence findings route to
debt. Reviewer approval therefore requires no HIGH/MEDIUM finding at or above 0.50.
Both review modes return one valid JSON object with an explicit result, never JSON
plus a trailing status token. VERIFY downgrades a clarification lacking new evidence
to debt, and routes a high-confidence in-scope repair regression to the circuit
breaker because the default two-call budget is already spent.
