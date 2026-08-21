# GW-010 — one plugin root supports both Claude Code and Codex
Status: accepted · 2026-08-21 · Amends: GW-003

**Ruling**: `plugin/` remains the single process-layer root and carries both
`.claude-plugin/plugin.json` and `.codex-plugin/plugin.json`; Codex reviewer
roles ship as skills that spawn fresh-context subagents, while Claude agents remain.
**Because**: duplicating or moving the plugin would create two drifting process
implementations, while Codex does not ingest Claude's `agents/` directory.
**Enforced by**: `plugin/tests/test_plugin_contracts.py`; both plugin validators.

---

## Context

Groundwork 0.4.0 was packaged only for Claude Code: its required manifest lived
under `.claude-plugin/`, its marketplace used Anthropic's schema, commands assumed
`CLAUDE_PLUGIN_ROOT`, and the four independent review roles lived only in
`plugin/agents/`. Codex plugins require `.codex-plugin/plugin.json`, discover
workflows from `skills/`, and use `.agents/plugins/marketplace.json` for a local or
Git-backed marketplace.

The repository already separates the reusable process layer (`plugin/`) from
project ground and enforcement. Making the repository root the Codex plugin would
package project state and violate that boundary; copying `plugin/` under a second
path would make every workflow change a synchronization problem.

## Decision

1. Keep `plugin/` as the only plugin root. Add the Codex manifest beside the
   Claude manifest and keep their name and semantic version identical.
2. Add a repository Codex marketplace at `.agents/plugins/marketplace.json` whose
   local source is `./plugin`. The same file makes the Git repository installable
   with `codex plugin marketplace add HaoweiChan/groundwork`.
3. Preserve `plugin/agents/` for Claude. Add skill counterparts for
   `cold-reviewer`, `eval-adversary`, `spec-drift`, and `pr-reviewer`; each wrapper
   explicitly delegates with `fork_turns: "none"` instead of inheriting the
   author's conversation. `pr-loop` invokes the registered Claude agent or
   bundled Codex skill according to the host.
4. Plugin skills resolve scripts and scaffold assets relative to their own
   installed skill path. The complete initializer scaffold ships under
   `plugin/assets/scaffold/`; skills do not depend on `CLAUDE_PLUGIN_ROOT` or the
   surrounding marketplace checkout.
5. Documentation names both invocation forms: `/skill` for Claude Code and
   `$skill` for Codex. Installation and update commands are tested against the
   checked-in repo marketplace.
6. Codex `pr-loop` creates and verifies an isolated Git worktree before spawning
   an implementer with no inherited conversation. Sharing the host filesystem is
   acceptable; sharing the orchestrator checkout is not.

## Alternatives rejected

- **Make the repository root the Codex plugin.** Rejected because project eval
  history, specs, tasks, and enforcement are ground/state, not distributable process.
- **Copy the plugin to `plugins/groundwork/`.** Rejected because two source trees
  would drift and double every review/eval change.
- **Drop independent agents on Codex.** Rejected because actor/evaluator separation
  is the verification architecture, not a Claude-specific convenience.

## Consequences

- A release changes two manifests but one implementation tree; an invariant checks
  the versions stay equal.
- Codex displays reviewer roles as skills rather than a native Claude-style agent
  registry, but the actual review still occurs in a no-history spawned context.
- The distributable package is larger because it contains the initializer
  scaffold, but installation is self-contained and cache-safe.
- Repo-local installation can be validated without publishing to a public catalog.
