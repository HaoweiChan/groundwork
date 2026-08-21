# GW-012 — pr-loop keeps its orchestrator on the frontier tier
Status: accepted · 2026-08-21 · Amends: GW-011

**Ruling**: Run the pr-loop orchestrator on Opus in Claude Code or
`gpt-5.6-sol` in Codex; economy routing applies only to bounded subagents.
**Because**: the orchestrator integrates incomplete evidence, detects risk,
routes models, and controls circuit breakers across the entire delivery state.
**Enforced by**: `plugin/tests/test_plugin_contracts.py`; repeated pr-loop
model-floor checks and the `orchestrator_checks` ledger trace.

---

## Context

GW-011 correctly reduced the cost of bounded implementer and reviewer work, but
did not explicitly state a floor for the parent orchestrator. A lower-tier parent
could misclassify task risk, create an underpowered review packet, or mishandle a
circuit breaker before any executable gate could catch the coordination error.

## Decision

- The Claude Code orchestrator runs on the `opus` alias.
- The Codex orchestrator runs on `gpt-5.6-sol`.
- The orchestrator confirms its effective model before entering SPEC, every later
  state transition, and every subagent spawn. A changed or economy model stops and
  asks the human to switch or restart; a hidden model signal requires confirmation.
- Only spawned, bounded roles use Sonnet, Terra, or Luna routing.
- The ledger stores every model-floor checkpoint in `orchestrator_checks`, separate
  from every subagent attempt in `model_routes`.

## Consequences

- The component making global risk and budget decisions retains frontier-level
  reasoning, while most task execution can still use less expensive models.
- Starting pr-loop from an economy-model session becomes a visible stop rather
  than a silent quality downgrade.

## Runtime evidence

OpenAI documents `gpt-5.6-sol` as its frontier model for complex professional
work: https://developers.openai.com/api/docs/models/gpt-5.6-sol
