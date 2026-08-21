"""Static package-contract adapter for the dual-runtime plugin."""
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PLUGIN = ROOT / "plugin"
ROLE_NAMES = ["cold-reviewer", "eval-adversary", "pr-reviewer", "spec-drift"]
SCAFFOLD_PATHS = [
    ".eval-baseline.json",
    ".claude/hooks/post-edit-invariant.sh",
    ".claude/settings.json",
    ".githooks/pre-commit",
    "tasks/TODO.md",
    "tasks/DONE.md",
    "evals/run.py",
    "evals/golden/.gitkeep",
    "evals/adversarial/.gitkeep",
    "evals/report/.gitkeep",
]


def _json(path):
    return json.loads(path.read_text())


def _compare(actual, expected):
    mismatches = {
        key: {"expected": value, "actual": actual.get(key)}
        for key, value in expected.items() if actual.get(key) != value
    }
    return {"passed": not mismatches, "mismatches": mismatches, "actual": actual}


def _package():
    codex = _json(PLUGIN / ".codex-plugin" / "plugin.json")
    claude = _json(PLUGIN / ".claude-plugin" / "plugin.json")
    marketplace = _json(ROOT / ".agents" / "plugins" / "marketplace.json")
    entry = next(item for item in marketplace["plugins"] if item["name"] == "groundwork")
    codex_version = codex.get("version", "")
    return {
        "manifest_name": codex.get("name"),
        "skills": codex.get("skills"),
        "versions_match": codex_version == claude.get("version")
                          and bool(re.fullmatch(r"\d+\.\d+\.\d+", codex_version)),
        "marketplace_name": marketplace.get("name"),
        "marketplace_source": entry.get("source", {}).get("path"),
        "installation": entry.get("policy", {}).get("installation"),
        "authentication": entry.get("policy", {}).get("authentication"),
    }


def _portability():
    references = []
    for path in sorted((PLUGIN / "skills").rglob("*")):
        if path.is_file() and "CLAUDE_PLUGIN_ROOT" in path.read_text(errors="ignore"):
            references.append(str(path.relative_to(ROOT)))
    readme = (ROOT / "README.md").read_text()
    return {
        "host_root_references": references,
        "readme_has_codex_install": "codex plugin marketplace add HaoweiChan/groundwork" in readme,
        "readme_has_codex_invocation": "$pr-loop" in readme and "$groundwork-init" in readme,
    }


def _roles():
    existing = []
    delegated = []
    for name in ROLE_NAMES:
        path = PLUGIN / "skills" / name / "SKILL.md"
        if not path.is_file():
            continue
        existing.append(name)
        text = path.read_text()
        if 'fork_turns: "none"' in text and f"../../agents/{name}.md" in text:
            delegated.append(name)
    return {"role_skills": existing, "all_delegate": delegated == ROLE_NAMES}


def _initializer_scaffold():
    scaffold = PLUGIN / "assets" / "scaffold"
    missing = [path for path in SCAFFOLD_PATHS if not (scaffold / path).is_file()]
    init_text = (PLUGIN / "skills" / "groundwork-init" / "SKILL.md").read_text()
    return {
        "missing_scaffold_paths": missing,
        "init_prefers_bundled_scaffold": bool(re.search(
            r"Always use\s+`<groundwork-plugin-root>/assets/scaffold`", init_text
        )),
    }


def _fresh_review_context():
    no_history = []
    for name in ROLE_NAMES:
        text = (PLUGIN / "skills" / name / "SKILL.md").read_text()
        if 'fork_turns: "none"' in text:
            no_history.append(name)
    pr_loop = (PLUGIN / "skills" / "pr-loop" / "SKILL.md").read_text()
    return {
        "role_skills_with_no_history": no_history,
        "pr_loop_review_no_history": 'reviewer with `fork_turns: "none"`' in pr_loop,
    }


def _worktree_isolation():
    text = (PLUGIN / "skills" / "pr-loop" / "SKILL.md").read_text()
    return {
        "creates_worktree_before_spawn": "git worktree add" in text,
        "implementer_uses_no_history": 'implementer with `fork_turns: "none"`' in text,
        "implementer_working_directory_is_explicit": "absolute worktree path" in text,
        "verifies_distinct_worktree": "git rev-parse --show-toplevel" in text,
    }


def run_case(case):
    check = case["input"]["check"]
    actual = {
        "package": _package,
        "portability": _portability,
        "roles": _roles,
        "initializer_scaffold": _initializer_scaffold,
        "fresh_review_context": _fresh_review_context,
        "worktree_isolation": _worktree_isolation,
    }[check]()
    return _compare(actual, case["expect"])
