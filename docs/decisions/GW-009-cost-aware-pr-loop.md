# GW-009 — pr-loop plans review deterministically and bounds model review calls
Status: accepted · 2026-08-21 · Amends: GW-001, GW-002, GW-005

**Ruling**: Before model review, run a deterministic change analysis and Ponytail
preflight; give reviewers only the resulting bounded context. One full/focused
review plus one delta verification is the default budget; a third call needs a human.
**Because**: repeated repository discovery and full-context agent handoffs dominate
verification cost without adding proportional evidence.
**Enforced by**: `plugin/skills/pr-loop/scripts/analyze.py`; `pr-loop` ANALYZE,
REVIEW, and VERIFY states; `plugin/tests/test_analyze.py`.

---

## Context

pr-loop v3 bounded PR chatter and stopped round 2+ from sweeping the full diff,
but it still paid for a fresh agent to rediscover the repository, understand the
impact surface, and restate every finding on each repair round. The loop was
correctness-aware but not verification-cost-aware. Its cost was approximately
the number of rounds multiplied by two large context ingestions: reviewer and
implementer.

Groundwork already has the right control mechanisms. Graphify can identify the
neighborhood of a changed component, Ponytail can challenge unnecessary surface
before review, and the eval gate can reject objective failures without spending
a reviewer call. They need to be state transitions and inputs, not optional
sentences in a prompt.

## Decision

1. After implementation and before review, a stdlib-only analyzer reads the diff
   once. It emits changed files and line counts, risk reasons, Ponytail questions,
   Graphify neighbors when `graphify-out/graph.json` exists, a bounded context-file
   allowlist, and `focused` or `full` review mode. It makes no model calls.
2. The implementer resolves the Ponytail questions before GATE: reuse existing
   code where possible, prefer stdlib, and justify every remaining new file,
   dependency, or abstraction. An unresolved question returns directly to the
   implementer; it does not spend a reviewer call.
3. GATE precedes review. A red gate returns directly to repair. A green gate and
   the analysis packet are the reviewer's inputs. The reviewer reads outside the
   allowlist only when it names the missing context and why it is necessary.
4. The first reviewer call is adaptive: focused for bounded low/medium-risk diffs,
   full across the analyzer's impacted surface for high-risk diffs. It checks in
   order: acceptance, invariants/gate evidence, changed behavior, then design.
5. Findings include confidence. Only in-scope HIGH/MEDIUM findings with confidence
   at least 0.80 block automatically. Confidence from 0.50 through 0.79 is returned
   once to the implementer for clarification and then either gains evidence or
   becomes debt; lower confidence is debt immediately.
6. Repairs are batched. The second reviewer call is delta verification: standing
   findings, resolution evidence, and the repair diff only. It is not another PR
   review. The default model-review-call budget is two. A third call is available
   only after the human explicitly chooses it at the circuit breaker.
7. The ledger records `review_calls`, `review_mode`, and actual reviewer token
   counts when the runtime exposes them. Unknown token counts are `null`, never
   estimates.

## Alternatives rejected

- **Use a cheaper model for the existing loop.** This lowers unit price while
  preserving redundant discovery and round count, the two structural cost drivers.
- **Always run Graphify semantic extraction before review.** The analysis phase
  itself would spend tokens. Existing graph data is consumed when present; the
  analyzer otherwise falls back to changed-file context without fabricating impact.
- **Skip independent review when the gate is green.** Evals encode known ground;
  a falsification pass is still needed to find missing cases and dishonest claims.
- **Let confidence override scope or evidence.** A high subjective number is not
  proof. Confidence only routes a finding after the existing evidence and scope
  requirements are met.

## Consequences

- Small green diffs normally spend one reviewer call; repaired diffs spend two.
- Review can miss an impact edge absent from Graphify. The packet says when it is
  using fallback data, and high-risk classification still permits a broader review.
- Ponytail remains a reasoning discipline, but the analyzer makes its questions
  unavoidable and records which changed surfaces require an answer.
- Review efficiency becomes measurable instead of anecdotal through the ledger.
