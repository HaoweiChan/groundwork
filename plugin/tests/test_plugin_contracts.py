"""Repository-level contracts for the distributable Groundwork plugin."""

import json
import re
import subprocess
import sys
import unittest
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


def read_json(path):
    return json.loads(path.read_text())


class PluginContractTests(unittest.TestCase):
    def test_codex_package_and_marketplace(self):
        codex = read_json(PLUGIN / ".codex-plugin" / "plugin.json")
        claude = read_json(PLUGIN / ".claude-plugin" / "plugin.json")
        marketplace = read_json(ROOT / ".agents" / "plugins" / "marketplace.json")
        entry = next(item for item in marketplace["plugins"] if item["name"] == "groundwork")

        self.assertEqual("groundwork", codex.get("name"))
        self.assertEqual("./skills/", codex.get("skills"))
        self.assertEqual(claude.get("version"), codex.get("version"))
        self.assertIsNotNone(re.fullmatch(r"\d+\.\d+\.\d+", codex.get("version", "")))
        self.assertEqual("groundwork", marketplace.get("name"))
        self.assertEqual("./plugin", entry.get("source", {}).get("path"))
        self.assertEqual("AVAILABLE", entry.get("policy", {}).get("installation"))
        self.assertEqual("ON_INSTALL", entry.get("policy", {}).get("authentication"))

    def test_skills_are_host_portable(self):
        references = [
            str(path.relative_to(ROOT))
            for path in sorted((PLUGIN / "skills").rglob("*"))
            if path.is_file() and "CLAUDE_PLUGIN_ROOT" in path.read_text(errors="ignore")
        ]
        readme = (ROOT / "README.md").read_text()

        self.assertEqual([], references)
        self.assertIn("codex plugin marketplace add HaoweiChan/groundwork", readme)
        self.assertIn("$pr-loop", readme)
        self.assertIn("$groundwork-init", readme)

    def test_codex_review_roles_delegate_without_history(self):
        for name in ROLE_NAMES:
            with self.subTest(role=name):
                text = (PLUGIN / "skills" / name / "SKILL.md").read_text()
                self.assertIn('fork_turns: "none"', text)
                self.assertIn(f"../../agents/{name}.md", text)

        pr_loop = (PLUGIN / "skills" / "pr-loop" / "SKILL.md").read_text()
        self.assertIn('reviewer with `fork_turns: "none"`', pr_loop)

    def test_initializer_uses_complete_bundled_scaffold(self):
        scaffold = PLUGIN / "assets" / "scaffold"
        missing = [path for path in SCAFFOLD_PATHS if not (scaffold / path).is_file()]
        init_text = (PLUGIN / "skills" / "groundwork-init" / "SKILL.md").read_text()

        self.assertEqual([], missing)
        self.assertRegex(
            init_text,
            re.compile(r"Always use\s+`<groundwork-plugin-root>/assets/scaffold`"),
        )

    def test_project_and_bundled_eval_runners_execute(self):
        for root in (ROOT, PLUGIN / "assets" / "scaffold"):
            with self.subTest(root=str(root)):
                result = subprocess.run(
                    [sys.executable, "-m", "evals.run", "--suite", "fast", "--no-report"],
                    cwd=root,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(0, result.returncode, result.stderr or result.stdout)

    def test_codex_implementer_uses_an_isolated_worktree(self):
        text = (PLUGIN / "skills" / "pr-loop" / "SKILL.md").read_text()

        self.assertIn("git worktree add", text)
        self.assertIn('implementer with `fork_turns: "none"`', text)
        self.assertIn("absolute worktree path", text)
        self.assertIn("git rev-parse --show-toplevel", text)


class PrLoopModelPolicyTests(unittest.TestCase):
    versioned_model_id = re.compile(
        r"\b(?:gpt-\d+(?:\.\d+)*(?:-[a-z0-9-]+)?|claude-[a-z0-9-]*\d[a-z0-9-]*)\b",
        re.IGNORECASE,
    )

    @classmethod
    def setUpClass(cls):
        cls.skill = (PLUGIN / "skills" / "pr-loop" / "SKILL.md").read_text()
        policy_paths = (
            ROOT / "README.md",
            ROOT / "CLAUDE.md",
            ROOT / "docs" / "groundwork.md",
            ROOT / "docs" / "decisions" / "GW-011-route-subagents-by-task-risk.md",
            ROOT / "docs" / "decisions" / "GW-012-frontier-orchestrator.md",
            ROOT / "docs" / "decisions" / "GW-014-capability-level-model-routing.md",
        )
        cls.model_policy = "\n".join(path.read_text() for path in policy_paths)

    def test_routes_every_subagent_to_the_least_expensive_adequate_model(self):
        self.assertIn("model-routing decision before every subagent spawn", self.skill)
        self.assertIn("`sonnet-level`", self.skill)
        self.assertIn("`terra-level`", self.skill)
        self.assertIn("`luna-level`", self.skill)
        self.assertIn("Resolve each level to a currently supported host model", self.skill)
        self.assertIn('"model_routes":[{"role":"implementer"', self.skill)

    def test_initial_risk_screen_precedes_implementer_spawn(self):
        screen = self.skill.find("run an initial risk screen")
        spawn = self.skill.find("Spawn the implementer")
        self.assertGreaterEqual(screen, 0)
        self.assertGreaterEqual(spawn, 0)
        self.assertLess(screen, spawn)
        for phrase in (
            "task block and acceptance criteria",
            "repository contracts/instructions",
            "existing Graphify graph",
            "Unknown initial risk uses the explicit high-capability level",
        ):
            self.assertIn(phrase, self.skill)

    def test_capability_levels_are_explicit(self):
        self.assertIn("`opus-level or stronger`", self.skill)
        self.assertIn("`sol-level or stronger`", self.skill)
        self.assertNotIn("host frontier/default", self.skill)

    def test_model_floor_uses_capability_levels_not_version_ids(self):
        """invariant-gap: model releases must not invalidate the capability floor."""
        self.assertIn("`opus-level or stronger`", self.skill)
        self.assertIn("`sol-level or stronger`", self.skill)
        self.assertIn("A newer or stronger tier always satisfies the floor", self.skill)
        self.assertRegex(self.skill, r"exact model ID\s+may be unavailable")
        self.assertIn("Ask only when the tier itself is", self.skill)
        self.assertIn("never merely because the versioned ID is hidden", self.skill)
        self.assertNotRegex(
            self.skill + self.model_policy,
            self.versioned_model_id,
        )

    def test_versioned_model_guard_covers_both_hosts(self):
        for model_id in ("gpt-5.6-sol", "claude-opus-4-1"):
            with self.subTest(model_id=model_id):
                self.assertRegex(model_id, self.versioned_model_id)

    def test_fallback_and_high_risk_routes_preserve_capability_floors(self):
        for phrase in (
            r"fallback must meet or exceed the\s+requested capability level",
            r"confirm the effective\s+capability tier for every high-capability route",
            r"If that tier is unknown,\s+stop for human routing",
        ):
            self.assertRegex(self.skill, phrase)

    def test_route_attempts_and_failures_are_recorded(self):
        for field in (
            "`model_routes`", "`role`", "`attempt`", "`requested`", "`effective`",
            "`risk`", "`reason`", "`outcome`",
        ):
            self.assertIn(field, self.skill)
        self.assertRegex(
            self.skill,
            re.compile(r"A reviewer invocation counts\s+toward the review-call budget even when it fails"),
        )

    def test_orchestrator_remains_frontier(self):
        self.assertIn("Claude Code: `opus-level or stronger`", self.skill)
        self.assertIn("Codex: `sol-level or stronger`", self.skill)
        self.assertIn("Model routing is subagent-only", self.skill)
        self.assertIn("stop and ask the human to switch/restart", self.skill)
        self.assertIn('"orchestrator_checks":[{"checkpoint":"SPEC"', self.skill)

    def test_orchestrator_floor_is_rechecked_and_recorded(self):
        self.assertIn(
            "re-confirm it before every later state transition and every subagent spawn",
            self.skill,
        )
        self.assertRegex(self.skill, r"If\s+the orchestrator changes to")
        self.assertRegex(self.skill, r"do\s+not begin or continue the state machine")
        for field in ("`orchestrator_checks`", "`checkpoint`", "`evidence`", "`verified_at`"):
            self.assertIn(field, self.skill)
        self.assertIn("MUST append every passed check to `orchestrator_checks`", self.skill)
        self.assertNotRegex(
            self.skill,
            re.compile(r"(?i)do not record[^.\n]{0,80}orchestrator"),
        )

    def test_orchestrator_is_never_permitted_to_use_economy_models(self):
        pattern = re.compile(
            r"(?i)orchestrator\s+(?:may|can|should|must|uses?|runs?)"
            r"[^.\n]{0,100}(?:sonnet|terra|luna)"
        )
        self.assertEqual([], pattern.findall(self.skill))


if __name__ == "__main__":
    unittest.main()
