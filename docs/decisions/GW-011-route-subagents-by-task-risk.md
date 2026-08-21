# GW-011 — pr-loop chooses the least expensive adequate subagent model
Status: accepted · 2026-08-21 · Amends: GW-009

**Ruling**: Before every subagent spawn, route bounded low/ordinary-risk work
to Sonnet-level on Claude Code or Luna-/Terra-level on Codex; require
Opus-level or stronger / Sol-level or stronger for high-risk, full-review,
cross-cutting, security/safety, or ambiguous work.
**Because**: role isolation and executable gates carry correctness, so routine
bounded work should not automatically pay frontier-model cost.
**Enforced by**: `plugin/tests/test_plugin_contracts.py`;
`plugin/skills/pr-loop/SKILL.md` model routing table and evidence ledger.

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

- Claude Code uses Sonnet-level models for mechanical, ordinary, and bounded work.
- Codex uses Luna-level for mechanical low-risk work and Terra-level for ordinary
  implementation, focused review, and delta verification.
- Opus-level or stronger on Claude Code and Sol-level or stronger on Codex remain
  mandatory for high-risk/full review, cross-cutting design, security or safety
  impact, unclear acceptance, and retry after a smaller model fails its bounded
  contract.
- An unavailable tier may fall back only to a known model at or above the
  requested capability level. Otherwise the loop stops for human routing.
- Every high-capability route needs evidence of its effective capability tier;
  a hidden exact model ID is acceptable, but an unknown tier is not.
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
- Capability levels remain stable when either runtime changes concrete model IDs;
  the host resolves the current model only when spawning.

## Runtime evidence

- Claude Code supports per-invocation subagent model selection:
  https://code.claude.com/docs/en/sub-agents
- OpenAI publishes its current model tiers at:
  https://developers.openai.com/api/docs/models
