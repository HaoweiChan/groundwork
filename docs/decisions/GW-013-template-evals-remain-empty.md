# GW-013 — keep Groundwork self-tests out of the project template
Status: accepted · 2026-08-21

**Ruling**: Keep root `evals/`, `src/`, and `specs/` as clean project seed
material; place Groundwork plugin contracts and regressions in `plugin/tests/`.
**Because**: the adopting project's eval set is its spec, so template-maintainer
history and implementation adapters are contamination rather than reusable ground.
**Enforced by**: `plugin/tests/test_repository_boundary.py`; source-repo hooks.

---

## Context

Groundwork initially used its own project eval harness to verify the plugin.
Every plugin feature added task adapters, adversarial JSON cases, and persistent
run history to the same directories that are presented as a clean project
template. The checks were useful, but their ownership was wrong: an adopting
project should begin with its own domain cases, not Groundwork's packaging and
orchestration history.

## Decision

1. Root `evals/`, `src/`, and `specs/` remain the seed copied or cloned for a
   new project. They do not contain Groundwork implementation adapters, plugin
   cases, or generated report history.
2. Groundwork's self-tests use Python's standard-library `unittest` under
   `plugin/tests/`. Related assertions are consolidated by behavior rather than
   stored as one JSON file per plugin contract.
3. The Groundwork source-repo pre-commit and post-edit hooks run the plugin test
   suite. The bundled scaffold retains the eval-first hooks for adopting projects.
4. A repository-boundary regression test prevents plugin checks from drifting
   back into the project template directories.

## Alternatives rejected

- **Keep deleting old eval history while adding new plugin cases.** This treats
  growth as a retention problem and leaves the ownership error intact.
- **Remove self-tests entirely.** Packaging, host parity, analyzer behavior, and
  model-routing policy still need executable protection.
- **Ship two complete templates.** A separate maintainer checkout would add
  synchronization work without improving the plugin/project boundary.

## Consequences

- The root scaffold stays small and starts with no Groundwork-specific cases or
  accumulated reports.
- Groundwork maintainers run one fast stdlib test command; descendant projects
  still use `evals/run.py` and define their own ground.
- Tests are packaged beside the plugin source, adding a small amount of source
  distribution size but no runtime dependency or loaded context.
