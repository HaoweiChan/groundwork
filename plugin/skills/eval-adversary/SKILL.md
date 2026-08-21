---
name: eval-adversary
description: Fresh-context adversarial eval analysis that finds real inputs missing from a green suite. Use when growing eval coverage or before milestones.
---

# eval-adversary — Codex role adapter

The canonical role contract is `../../agents/eval-adversary.md`, resolved from
this skill directory. Read it completely before acting.

- If the task prompt explicitly designates you as the fresh adversary, execute the
  canonical contract directly and do not delegate again.
- Otherwise spawn exactly one subagent with `fork_turns: "none"`; do not use the
  runtime default, which inherits the author conversation. Its initial task is the
  complete bounded packet: task contract, eval scope, and instructions to read this
  skill and canonical contract. Return its evidence/case candidates unchanged.
- The role never fixes production code or weakens an invariant.
