# 000 — Invariants

Properties that must ALWAYS hold, across every task in this repo.
**An invariant listed here without a backing eval case (tagged
`"suites": ["invariant"]`) is decorative and counts as drift** — the
`spec-drift` agent flags it.

Format per invariant:

```
## INV-<n>: <one-line property>
- Rationale: why this must never break
- Enforced by: evals/<...>.json (case id)
```

## INV-0: The pipeline never reports success with empty output
- Rationale: silent failure is the #1 graded failure mode; an empty result
  must surface as an explicit failure/low-confidence signal, never a green run.
- Enforced by: (pending — first task-specific case must cover this)

---

Task-specific invariants live below a `## <task>` heading as tasks are added.

## pr_loop_analysis

## INV-1: A non-empty PR diff always yields bounded review context without invented impact
- Rationale: an empty or fabricated analysis either restores repository-wide reviewer discovery or misdirects verification.
- Enforced by: `evals/adversarial/pr-loop-analysis-new-surface.json` (`pr-loop-analysis-new-surface`)

## INV-2: Reviewer approval and orchestrator confidence routing use the same threshold
- Rationale: contradictory approval can both spend a needless verification call and publish an approved result with unresolved clarification findings.
- Enforced by: `evals/adversarial/pr-loop-review-confidence-routing.json` (`pr-loop-review-confidence-routing`)

## INV-3: Change analysis never drops review context while reporting success
- Rationale: misparsed paths, partial preflight resolutions, and missed dependency manifests silently under-scope review.
- Enforced by: `pr-loop-analysis-git-quoted-path`, `pr-loop-analysis-preflight-all-files`, `pr-loop-analysis-pipfile`

## INV-4: Reviewer output and post-VERIFY routing are deterministic
- Rationale: invalid JSON or an unrouteable result costs manual recovery or another model call.
- Enforced by: `pr-loop-review-protocol-envelope`

## codex_plugin

## INV-5: The distributable process layer installs on Claude Code and Codex without behavioral forks
- Rationale: duplicated implementations or missing reviewer roles make verification depend on which host runs it.
- Enforced by: `codex-plugin-package`, `codex-plugin-portability`, `codex-plugin-review-role-parity`, `codex-plugin-initializer-scaffold`, `codex-plugin-fresh-review-context`, `codex-plugin-worktree-isolation`
