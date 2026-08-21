---
name: pr-reviewer
description: Fresh-context, cost-bounded falsification and delta verification role for Groundwork pr-loop. Use only for independent PR review or repair verification.
---

# pr-reviewer — Codex role adapter

The canonical role contract is `../../agents/pr-reviewer.md`, resolved from this
skill directory. Read it completely before acting.

- If the task prompt explicitly designates you as the fresh `mode: review` or
  `mode: verify` reviewer, execute the canonical contract directly and do not
  delegate again.
- Otherwise spawn exactly one subagent with `fork_turns: "none"`; do not use the
  runtime default, which inherits the author conversation. Its initial task is the
  complete bounded packet for the requested mode plus instructions to read this
  skill and canonical contract. Return its JSON envelope unchanged.
- The author and pr-loop orchestrator may not perform this review themselves.
