---
name: pr-loop-analysis-domain
description: Domain rules for the deterministic pr-loop change-intelligence packet.
---

# pr-loop analysis domain

- Treat the unified diff as the authority for changed paths and line counts.
- Treat Graphify as evidence, not an oracle: consume an existing `graph.json` but
  never trigger semantic extraction or fabricate neighbors.
- Keep output deterministic and bounded. Changed files precede derived context;
  sort all graph-derived collections.
- Risk is review routing, not a correctness verdict. High risk selects full review;
  it does not fail the PR.
- Ponytail checks are questions that the implementer must resolve before model
  review; syntax alone cannot decide whether a new abstraction is justified.
