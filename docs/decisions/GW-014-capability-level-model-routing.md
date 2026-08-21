# GW-014 — model routing names capability floors, not product versions
Status: accepted · 2026-08-21 · Amends: GW-011, GW-012

**Ruling**: Express Claude routing as Sonnet-/Opus-level and Codex routing as
Luna-/Terra-/Sol-level; “or stronger” satisfies every floor. Resolve concrete
model IDs only at spawn time.
**Because**: product names and versions change, and new tiers can appear above
the former frontier without weakening the intended capability floor.
**Enforced by**: `plugin/tests/test_plugin_contracts.py`;
`plugin/skills/pr-loop/SKILL.md` model checks, routing table, and evidence ledger.

---

## Context

GW-011 and GW-012 wrote current model aliases into the protocol. That turns a
capability requirement into a brittle allowlist: a routine model release can make
the wording stale, while a newly introduced tier above the named frontier may be
incorrectly rejected. Some runtimes also expose a selected capability tier without
revealing the exact effective model ID.

## Decision

- Normative policy names capability levels, never a product/version allowlist.
- Claude requires Opus-level or stronger and Codex requires Sol-level or stronger
  for orchestration and high-risk/full-review work. A newer stronger tier always
  qualifies.
- Bounded work routes to Sonnet-level on Claude or Luna-/Terra-level on Codex.
  At spawn time, the host resolves the requested level to a currently supported
  model. A fallback must meet or exceed the requested capability floor.
- Orchestrator checks accept exposed tier metadata, the host session selector, or
  human confirmation. They ask only when the tier itself is unknown, not merely
  because an exact versioned ID is hidden.
- The ledger records the requested capability level, the effective model when
  exposed, and the evidence used for each check or route. A hidden model ID is
  recorded as `null`; it is not silently guessed. A high-capability subagent route
  stops if its effective tier cannot be confirmed.

## Consequences

- Model releases do not invalidate the protocol or require an ADR just to rename
  a current product.
- The runtime integration remains responsible for mapping capability levels to
  available model IDs.
- Concrete model names may appear in runtime evidence, but never define the
  normative floor.

## Runtime evidence

Anthropic's current catalog places a tier above Opus, demonstrating why “Opus”
must be a floor rather than a maximum:
https://platform.claude.com/docs/en/about-claude/models/overview

OpenAI's current catalog similarly separates flagship, balanced, and
cost-sensitive tiers; those concrete names are runtime examples, not this ADR's
contract:
https://developers.openai.com/api/docs/models
