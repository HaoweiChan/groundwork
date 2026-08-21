"""Behavioral contracts for pr-loop's deterministic analysis packet."""

import importlib.util
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PLUGIN = ROOT / "plugin"
ANALYZER = PLUGIN / "skills" / "pr-loop" / "scripts" / "analyze.py"


def load_analyzer():
    spec = importlib.util.spec_from_file_location("pr_loop_analyzer", ANALYZER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {ANALYZER}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def diff(value):
    return textwrap.dedent(value).lstrip()


class AnalyzeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.analyzer = load_analyzer()

    def assert_fields(self, result, expected):
        actual = {
            "files": result["change"]["files"],
            "added": result["change"]["lines_added"],
            "deleted": result["change"]["lines_deleted"],
            "risk": result["risk"]["level"],
            "review_mode": result["review"]["mode"],
            "question_ids": [item["id"] for item in result["preflight"]["questions"]],
            "preflight_status": result["preflight"]["status"],
            "unresolved_files": result["preflight"].get("unresolved_files", []),
            "impact_source": result["impact"]["source"],
            "changed_nodes": result["impact"]["changed_nodes"],
            "affected_nodes": result["impact"]["affected_nodes"],
            "context_files": result["review"]["context_files"],
        }
        for key, value in expected.items():
            self.assertEqual(value, actual[key], key)

    def test_new_source_and_dependency_require_full_review(self):
        result = self.analyzer.analyze(diff("""
            diff --git a/src/report.py b/src/report.py
            new file mode 100644
            --- /dev/null
            +++ b/src/report.py
            @@ -0,0 +1,2 @@
            +import requests
            +def build(): return requests.get('https://example.test')
            diff --git a/requirements.txt b/requirements.txt
            index 1111111..2222222 100644
            --- a/requirements.txt
            +++ b/requirements.txt
            @@ -1,0 +2 @@
            +requests==2.32.0
        """))
        self.assert_fields(result, {
            "files": ["src/report.py", "requirements.txt"],
            "added": 3,
            "risk": "high",
            "review_mode": "full",
            "question_ids": ["new-source-surface", "dependency-change"],
            "preflight_status": "resolve",
            "impact_source": "changed-files",
        })

    def test_pipfile_is_a_dependency_surface(self):
        result = self.analyzer.analyze(diff("""
            diff --git a/Pipfile b/Pipfile
            index 1111111..2222222 100644
            --- a/Pipfile
            +++ b/Pipfile
            @@ -1,0 +2 @@
            +requests = "*"
            diff --git a/evals/adversarial/http.json b/evals/adversarial/http.json
            new file mode 100644
            --- /dev/null
            +++ b/evals/adversarial/http.json
            @@ -0,0 +1 @@
            +{}
        """))
        self.assert_fields(result, {
            "question_ids": ["dependency-change"],
            "preflight_status": "resolve",
            "risk": "high",
            "review_mode": "full",
        })

    def test_preflight_resolves_each_new_file(self):
        result = self.analyzer.analyze(
            diff("""
                diff --git a/src/alpha.py b/src/alpha.py
                new file mode 100644
                --- /dev/null
                +++ b/src/alpha.py
                @@ -0,0 +1 @@
                +ALPHA = 1
                diff --git a/src/beta.py b/src/beta.py
                new file mode 100644
                --- /dev/null
                +++ b/src/beta.py
                @@ -0,0 +1 @@
                +BETA = 2
            """),
            resolutions={"new-source-surface": {"files": {
                "src/alpha.py": {"outcome": "justified", "reason": "Required."},
            }}},
        )
        self.assert_fields(result, {
            "question_ids": ["new-source-surface"],
            "preflight_status": "resolve",
            "unresolved_files": ["src/beta.py"],
        })

    def test_preflight_accepts_a_legacy_whole_question_resolution(self):
        result = self.analyzer.analyze(
            diff("""
                diff --git a/src/helper.py b/src/helper.py
                new file mode 100644
                --- /dev/null
                +++ b/src/helper.py
                @@ -0,0 +1 @@
                +VALUE = 1
            """),
            resolutions={"new-source-surface": {
                "outcome": "justified",
                "reason": "The task introduces the first implementation module.",
            }},
        )
        self.assert_fields(result, {
            "files": ["src/helper.py"],
            "question_ids": ["new-source-surface"],
            "preflight_status": "pass",
        })

    def test_graph_limits_review_context_to_direct_neighbors(self):
        graph = {
            "nodes": [
                {"id": "parser_parse", "label": "Parser.parse", "source_file": "src/parser.py"},
                {"id": "normalizer", "label": "Normalizer", "source_file": "src/normalize.py"},
                {"id": "search_api", "label": "SearchAPI", "source_file": "src/api.py"},
            ],
            "edges": [
                {"source": "parser_parse", "target": "normalizer", "relation": "calls"},
                {"source": "normalizer", "target": "search_api", "relation": "calls"},
            ],
        }
        result = self.analyzer.analyze(diff("""
            diff --git a/src/parser.py b/src/parser.py
            index 1111111..2222222 100644
            --- a/src/parser.py
            +++ b/src/parser.py
            @@ -1 +1 @@
            -old = True
            +old = False
        """), graph=graph)
        self.assert_fields(result, {
            "files": ["src/parser.py"],
            "added": 1,
            "deleted": 1,
            "impact_source": "graphify",
            "changed_nodes": ["parser_parse"],
            "affected_nodes": ["normalizer"],
            "context_files": ["src/parser.py", "src/normalize.py"],
        })

    def test_git_quoted_unicode_paths_are_decoded(self):
        graph = {
            "nodes": [
                {"id": "zhong", "label": "Chinese module", "source_file": "src/中.py"},
                {"id": "caller", "label": "Caller", "source_file": "src/caller.py"},
            ],
            "edges": [{"source": "caller", "target": "zhong", "relation": "calls"}],
        }
        raw_diff = (
            'diff --git "a/src/\\344\\270\\255.py" "b/src/\\344\\270\\255.py"\n'
            'index 1111111..2222222 100644\n'
            '--- "a/src/\\344\\270\\255.py"\n'
            '+++ "b/src/\\344\\270\\255.py"\n'
            '@@ -1 +1 @@\n-old = True\n+old = False\n'
        )
        result = self.analyzer.analyze(raw_diff, graph=graph)
        self.assert_fields(result, {
            "files": ["src/中.py"],
            "impact_source": "graphify",
            "changed_nodes": ["zhong"],
            "affected_nodes": ["caller"],
            "context_files": ["src/中.py", "src/caller.py"],
        })


class ReviewProtocolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.skill = (PLUGIN / "skills" / "pr-loop" / "SKILL.md").read_text()
        cls.reviewer = (PLUGIN / "agents" / "pr-reviewer.md").read_text()

    def test_confidence_routes_to_repair_clarify_or_debt(self):
        self.assertIn("confidence at least 0.50", self.reviewer)
        for route in ("repair", "clarify", "debt"):
            self.assertIn(f"`{route}`", self.skill)

    def test_review_envelope_and_circuit_breaker_are_defined(self):
        self.assertIn('"result":"APPROVED|REQUEST_CHANGES"', self.reviewer)
        self.assertIn('"result":"APPROVED|OPEN"', self.reviewer)
        self.assertIn("clarification without new evidence becomes `DEBT`", self.reviewer)
        self.assertIn("repair-regression` opens the circuit breaker", self.skill)


if __name__ == "__main__":
    unittest.main()
