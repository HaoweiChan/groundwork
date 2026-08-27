# GW-015 — after call 2, pr-loop converges automatically instead of asking
Status: accepted · 2026-08-27 · Amends: GW-002, GW-005, GW-009

**Ruling**: After the default two review calls, an open in-scope finding no longer stops the loop for a human choice — the orchestrator enters convergence mode on its own.
Only findings where merging would be dishonest or harmful (red gate, real HIGH wrong-output, or a false published claim) stay BLOCKING and may spend further bounded calls; everything else is demoted to prioritized `## Debt`.
The circuit breaker still exists, narrowed to true anomalies: defect-moved, dispute, or convergence attempting to demote a HIGH.
**Because**: real deliveries show a predictable "continue" answer at the
breaker most of the time — a predictable answer is ceremony, not judgment,
and the two escalations that were never predictable (defect-moved, genuine
dispute) are the ones worth keeping.
**Enforced by**: `plugin/skills/pr-loop/SKILL.md` § 7 VERIFY (Convergence
mode), § 8 EVIDENCE, § tasks/TODO.md format; `plugin/skills/pr-loop/scripts/ready.py`.

---

## Context

GW-009 gave pr-loop a default two-call review budget and a circuit breaker for
whatever survives it: any open in-scope finding after call 2 stops the loop and
asks the human to explicitly choose a third call (option A) or accept
disposition/debt (option B). Real task deliveries run through this loop
(`DONE.md`-tracked browser-agent work) show a median of 4-6 rounds per task with
1-2 breaker prompts each — and the human's answer at the breaker is almost
always "continue," not a real fork in the road. A predictable answer means the
escalation itself was the cost, not the decision it produced: the human was
being interrupted mid-flow to restate a default.

The two exceptions in that same history are not predictable: a finding that
survives a repair attempt and reappears in the same shape (the defect moved,
it didn't resolve), and an implementer-rejected finding verification re-raises
with genuinely new evidence (a real dispute about the facts). Those are the
escalations worth a human's attention; the rest were the loop asking permission
to do the obviously right thing.

Meanwhile GW-002 already established that a finding blocks only if it's this
task's problem, with a severity-blind scope test — but it drew no line between
"real but not merge-blocking" (correctly routed to debt already) and "real and
merge-blocking but not resolved in two calls" (routed to a human prompt instead
of debt, purely because of *when* it was found, not *what* it is).

## Decision

1. **Convergence mode replaces the ask-every-time breaker.** After call 2, an
   open in-scope finding puts the orchestrator into convergence mode
   automatically — no human prompt to enter it. This is not a bigger budget;
   it is a narrower one applied without asking.
2. **BLOCKING narrows to three concrete conditions**: the gate is red; a
   HIGH-severity finding is wrong output on realistic input (shipped behavior
   is actually wrong, not merely undertested); or a published number/claim in
   the docs being merged is actively false. Only these may consume further
   bounded repair/verification calls — same batching rules as GW-002/GW-009,
   not an open-ended round count.
3. **Everything else is demoted, not asked about.** An open in-scope finding
   outside the BLOCKING set becomes a `## Debt` task block with
   `Origin: PR #<n> <finding-id> (converged)` and a mandatory `Priority:` —
   demoted MEDIUM becomes P1, demoted LOW becomes P2. The demotion is recorded
   in the finding's resolution artifact as route `debt`, reason `converged`,
   visible in the round comment and PR body like any other debt route — GW-005's
   bounded-comment/committed-JSON split is unchanged, convergence just adds one
   more route value.
4. **The breaker still exists, narrowed to true anomalies**: the same BLOCKING
   finding surviving two repair attempts (defect-moved); an implementer-rejected
   finding re-raised by verification with new concrete evidence (dispute); or
   convergence attempting to demote a HIGH (high-blocked — a HIGH never
   silently becomes debt, it either repairs or reaches the human). Anything
   else proceeds straight to EVIDENCE.
5. **P1 convergence debt is immediately runnable, not a stub.** At EVIDENCE,
   every P1 task block created by convergence carries a real `Spec` (from the
   finding's claim + evidence) and `Acceptance` (from the finding's acceptance
   field), and the human handoff message lists each as
   `follow-up: /pr-loop <id>` — the point of demoting is that the important
   remainder ships as its own PR, not that it rots as a one-line pointer.
6. **Priority is now a first-class task-block field.** `tasks/TODO.md` blocks
   gain an optional `Priority: P1|P2|P3` line (default P2, mandatory on
   `## Debt`). `ready.py` sorts ready output by `(priority, id)`; positional
   Queue order stays the primary signal for blocks that omit it.
7. **The ledger measures convergence, not just its inputs.** `converged`
   records the count of findings convergence demoted on this PR; `escalations`
   lists one entry per breaker trip with its `reason`
   (`defect-moved|dispute|high-blocked`). A PR with `converged: 0` and
   `escalations: []` reached EVIDENCE the old way — the two fields make the
   new behavior visible in the same evidence trail GW-009 already required.

## Alternatives rejected

- **Raise the default budget past two calls.** The owner's framing is explicit
  that this is not the fix: a bigger fixed budget still asks the same
  predictable question, just later, and still burns calls on findings that
  were never going to block a competent merge.
- **Drop the circuit breaker entirely.** Rejected — defect-moved and dispute
  are real signals that something is not converging normally; removing the
  escalation path would silently let those two failure modes merge unexamined.
- **Let convergence demote HIGH findings like any other severity.** Rejected
  by the same honesty floor GW-000/GW-002 already set: a HIGH is wrong-output-
  on-realistic-input by definition, so silently shipping it as "debt" would be
  the dishonest-merge failure mode the whole scope boundary exists to prevent.
- **Score-based auto-merge with no breaker at all.** Rejected — defect-moved
  and dispute are exactly the cases where a human's judgment is cheaper and
  more reliable than another model call, so removing the escalation path
  entirely trades a rare, valuable interruption for none.

## Consequences

- A converged PR now reaches EVIDENCE without a human round-trip whenever no
  BLOCKING finding remains — the common case, per the observed 4-6-round
  data, stops paying for a breaker prompt it always answered the same way.
- `## Debt` grows faster and with real priority signal instead of undifferentiated
  entries; P1 items are pre-specified enough to run through `/pr-loop` directly.
- The ledger's `converged`/`escalations` fields make "how often does
  convergence actually demote something, and how often does it still need a
  human" measurable instead of anecdotal, the same discipline GW-009 applied
  to review cost.
- A HIGH finding can still stall a merge past call 2 — that is intentional;
  convergence trades ceremony for speed, not honesty for speed.
