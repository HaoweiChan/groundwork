---
name: cold-reviewer
description: Fresh-context, evidence-only review for the three most likely silent failure inputs. Use after implementing or materially changing a pipeline stage.
---

# cold-reviewer — Codex role adapter

The canonical role contract is `../../agents/cold-reviewer.md`, resolved from
this skill directory. Read it completely before acting.

- If the task prompt explicitly designates you as the fresh reviewer, execute the
  canonical contract directly and do not delegate again.
- Otherwise spawn exactly one subagent with `fork_turns: "none"`; do not use the
  runtime default, which inherits the author conversation. Its initial task is the
  complete bounded packet: target paths, eval scope, and instructions to read this
  skill and canonical contract. Return its evidence unchanged. The
  author/coordinator may not perform the cold review.
- Never edit code in this role. Findings become adversarial cases in the parent
  workflow before implementation changes.
