---
name: spec-drift
description: Fresh-context, read-only audit of drift between invariants, contracts, ADRs, project instructions, and implementation.
---

# spec-drift — Codex role adapter

The canonical role contract is `../../agents/spec-drift.md`, resolved from this
skill directory. Read it completely before acting.

- If the task prompt explicitly designates you as the fresh drift auditor, execute
  the canonical contract directly and do not delegate again.
- Otherwise spawn exactly one subagent with `fork_turns: "none"`; do not use the
  runtime default, which inherits the author conversation. Its initial task is the
  complete bounded packet: target task or repository scope plus instructions to
  read this skill and canonical contract. Return its evidence unchanged.
- This role is read-only and never repairs the drift it reports.
