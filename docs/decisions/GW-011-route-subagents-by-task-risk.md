# GW-011 — pr-loop chooses the least expensive adequate subagent model
Status: accepted · 2026-08-21 · Amends: GW-009

**Ruling**: Before every subagent spawn, route bounded low/ordinary-risk work
to Sonnet on Claude Code or Luna/Terra on Codex; explicitly request Opus or Sol
for high-risk, full-review, cross-cutting, security/safety, or ambiguous work.
**Because**: role isolation and executable gates carry correctness, so routine
bounded work should not automatically pay frontier-model cost.
**Enforced by**: `pr-loop-model-routing*`; `plugin/skills/pr-loop/SKILL.md` model
routing table and evidence ledger.

---

## Context

GW-009 bounded reviewer calls and context, but every subagent could still inherit
the host's most expensive model. Mechanical implementation, focused review, and
delta verification have narrow inputs and machine-checked outputs; using the same
model tier as a security-sensitive full review wastes the savings from the rest of
the protocol.

## Decision

The orchestrator makes a visible routing choice before each spawn. Before the
first implementer it screens the task, acceptance, referenced paths, repo
contracts, dependency manifests, and any existing graph; unknown risk is high:

- Claude Code uses Sonnet for mechanical, ordinary, and bounded work.
- Codex uses Luna for mechanical low-risk work and Terra for ordinary
  implementation, focused review, and delta verification.
- Opus on Claude Code and `gpt-5.6-sol` on Codex remain mandatory for high-risk/full review,
  cross-cutting design, security or safety impact, unclear acceptance, and retry
  after a smaller model fails its bounded contract.
- An unavailable economy tier may fall back to the host default and is recorded.
  An unavailable explicit frontier tier stops for human routing.
- The ledger records every requested/effective model, reason, risk, outcome, and
  failed or substituted retry. A failed reviewer attempt still consumes a call.
  Model selection never changes the two-call budget, fresh-context rule, worktree
  isolation, gate, or reviewer independence.

## Consequences

- Routine PR rounds use less expensive inference without weakening deterministic
  verification; actual token totals remain separately measured.
- Evidence packs expose whether costly model use was justified.
- Initial risk screening is conservative because implementation-time diff analysis
  cannot retroactively upgrade an implementer that already ran.
- Host model names are explicit operational aliases and may require a later ADR
  when either runtime changes its available tiers.

## Runtime evidence

- Claude Code supports per-invocation subagent model aliases including `sonnet`
  and `opus`: https://code.claude.com/docs/en/sub-agents
- OpenAI identifies `gpt-5.6-terra` as the balance tier, `gpt-5.6-luna` as the
  cost-sensitive tier, and `gpt-5.6-sol` as frontier:
  https://developers.openai.com/api/docs/models
