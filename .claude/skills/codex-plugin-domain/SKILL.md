---
name: codex-plugin-domain
description: Domain rules for Groundwork's dual Claude Code and Codex plugin packaging.
---

# Codex plugin packaging domain

- Keep `plugin/` as the sole implementation root; manifests may differ by host,
  process skills may not.
- Follow OpenAI's `.codex-plugin/plugin.json` schema and repo marketplace schema.
- Codex has no Claude `agents/` ingestion contract: expose equivalent role skills
  that explicitly delegate to fresh subagents.
- Use the plugin/skill's discovered filesystem location, never a host-specific root
  environment variable, for bundled scripts and assets.
- Keep both manifests on the same strict-semver release.
