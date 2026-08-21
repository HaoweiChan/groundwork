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


def _model_routing():
    text = (PLUGIN / "skills" / "pr-loop" / "SKILL.md").read_text()
    return {
        "routes_before_every_spawn": (
            "model-routing decision before every subagent spawn" in text
        ),
        "claude_economy_model": "sonnet" if '`sonnet`' in text else None,
        "codex_economy_models": [
            model for model in ["gpt-5.6-terra", "gpt-5.6-luna"]
            if f"`{model}`" in text
        ],
        "preserves_frontier_for_high_risk": (
            "Use explicit frontier aliases for every high-risk condition" in text
        ),
        "records_selected_models": '"model_routes":[{"role":"implementer"' in text,
    }


def _model_routing_preanalysis():
    text = (PLUGIN / "skills" / "pr-loop" / "SKILL.md").read_text()
    screen = text.find("run an initial risk screen")
    spawn = text.find("Spawn the implementer")
    return {
        "initial_risk_before_implementer": 0 <= screen < spawn,
        "initial_risk_uses_task_and_repo_evidence": all(phrase in text for phrase in [
            "task block and acceptance criteria",
            "repository contracts/instructions",
            "existing Graphify graph",
        ]),
        "unknown_initial_risk_uses_frontier": (
            "Unknown initial risk uses the explicit frontier model" in text
        ),
    }


def _model_routing_explicit_frontier():
    text = (PLUGIN / "skills" / "pr-loop" / "SKILL.md").read_text()
    return {
        "claude_frontier_model": "opus" if "`opus`" in text else None,
        "codex_frontier_model": (
            "gpt-5.6-sol" if "`gpt-5.6-sol`" in text else None
        ),
        "does_not_inherit_frontier": "host frontier/default" not in text,
    }


def _model_routing_trace():
    text = (PLUGIN / "skills" / "pr-loop" / "SKILL.md").read_text()
    return {
        "records_route_attempts": all(field in text for field in [
            "`model_routes`", "`role`", "`attempt`", "`requested`", "`effective`",
        ]),
        "records_reason_and_outcome": all(field in text for field in [
            "`risk`", "`reason`", "`outcome`",
        ]),
        "failed_review_attempt_counts": bool(re.search(
            r"A reviewer invocation counts\s+toward the review-call budget even when it fails",
            text,
        )),
    }


def _orchestrator_frontier():
    text = (PLUGIN / "skills" / "pr-loop" / "SKILL.md").read_text()
    return {
        "claude_orchestrator": (
            "opus" if "Claude Code orchestrator: `opus`" in text else None
        ),
        "codex_orchestrator": (
            "gpt-5.6-sol" if "Codex orchestrator: `gpt-5.6-sol`" in text else None
        ),
        "routing_is_subagent_only": "Model routing is subagent-only" in text,
        "economy_orchestrator_stops": (
            "stop and ask the human to switch/restart" in text
        ),
        "ledger_records_orchestrator": (
            '"orchestrator_checks":[{"checkpoint":"SPEC"' in text
        ),
    }


def _orchestrator_runtime_fallback():
    text = (PLUGIN / "skills" / "pr-loop" / "SKILL.md").read_text()
    return {
        "rechecks_every_transition_and_spawn": (
            "re-confirm it before every later state transition and every subagent spawn" in text
        ),
        "model_change_stops": (
            "If the orchestrator changes model" in text
            and "do not begin or continue the state machine" in text
        ),
        "records_checkpoint_trace": all(field in text for field in [
            "`orchestrator_checks`", "`checkpoint`", "`verified_at`",
        ]),
    }


def _orchestrator_policy_conflict():
    text = (PLUGIN / "skills" / "pr-loop" / "SKILL.md").read_text()
    pattern = re.compile(
        r"(?i)orchestrator\s+(?:may|can|should|must|uses?|runs?)"
        r"[^.\n]{0,100}(?:sonnet|terra|luna)"
    )
    return {"economy_orchestrator_permissions": pattern.findall(text)}


def _orchestrator_ledger_directive():
    text = (PLUGIN / "skills" / "pr-loop" / "SKILL.md").read_text()
    return {
        "operational_append_required": (
            "MUST append every passed check to `orchestrator_checks`" in text
        ),
        "sample_has_checkpoint_trace": (
            '"orchestrator_checks":[{"checkpoint":"SPEC"' in text
        ),
        "no_negative_recording_rule": not bool(re.search(
            r"(?i)do not record[^.\n]{0,80}orchestrator", text
        )),
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
        "model_routing": _model_routing,
        "model_routing_preanalysis": _model_routing_preanalysis,
        "model_routing_explicit_frontier": _model_routing_explicit_frontier,
        "model_routing_trace": _model_routing_trace,
        "orchestrator_frontier": _orchestrator_frontier,
        "orchestrator_runtime_fallback": _orchestrator_runtime_fallback,
        "orchestrator_policy_conflict": _orchestrator_policy_conflict,
        "orchestrator_ledger_directive": _orchestrator_ledger_directive,
    }[check]()
    return _compare(actual, case["expect"])
