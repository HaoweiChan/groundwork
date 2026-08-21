# 002 — Codex plugin package contract

The reusable process layer at `plugin/` is installable in both Claude Code and
Codex without duplicating implementation files.

- `plugin/.codex-plugin/plugin.json` exists, names `groundwork`, points at
  `./skills/`, and has the same strict-semver version as the Claude manifest.
- `.agents/plugins/marketplace.json` names the `groundwork` marketplace and exposes
  one available, on-install-authenticated `groundwork` entry at `./plugin`.
- Every existing process skill remains discoverable. The four evidence-only Claude
  agents also have Codex skill counterparts that explicitly spawn a no-history
  subagent and preserve their read-only/evidence-only role.
- Installed skills do not require `CLAUDE_PLUGIN_ROOT`; scripts and scaffold sources
  resolve from the selected skill/plugin location.
- The package bundles the complete additive initializer scaffold; initialization
  never reaches outside the installed plugin directory for source files.
- Codex creates a distinct Git worktree before spawning the implementer, passes its
  absolute path as the mandatory working directory, and verifies it differs from
  the orchestrator checkout. Review/adversary roles use `fork_turns: "none"` and
  receive only their bounded initial packet.
- README documents both installation paths and uses `/name` for Claude Code versus
  `$name` for Codex.

The Codex manifest and marketplace must pass the bundled plugin validator and the
current `codex plugin marketplace` ingestion path.
