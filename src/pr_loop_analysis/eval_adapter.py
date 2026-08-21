"""Evaluate the plugin's portable pr-loop analyzer against contract cases."""
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ANALYZER = ROOT / "plugin" / "skills" / "pr-loop" / "scripts" / "analyze.py"


def _load_analyzer():
    spec = importlib.util.spec_from_file_location("pr_loop_analyzer", ANALYZER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {ANALYZER}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_case(case):
    if case["input"].get("protocol_check") == "review-confidence":
        skill = (ROOT / "plugin" / "skills" / "pr-loop" / "SKILL.md").read_text()
        reviewer = (ROOT / "plugin" / "agents" / "pr-reviewer.md").read_text()
        actual = {
            "approval_threshold": "0.50" if "confidence at least 0.50" in reviewer else "other",
            "routes": [route for route in ("repair", "clarify", "debt")
                       if f"`{route}`" in skill],
        }
        expect = case["expect"]
        mismatches = {
            key: {"expected": value, "actual": actual.get(key)}
            for key, value in expect.items() if actual.get(key) != value
        }
        return {"passed": not mismatches, "mismatches": mismatches, "actual": actual}

    if case["input"].get("protocol_check") == "review-envelope":
        skill = (ROOT / "plugin" / "skills" / "pr-loop" / "SKILL.md").read_text()
        reviewer = (ROOT / "plugin" / "agents" / "pr-reviewer.md").read_text()
        actual = {
            "single_json_envelope": all(text in reviewer for text in (
                '"result":"APPROVED|REQUEST_CHANGES"',
                '"result":"APPROVED|OPEN"',
            )),
            "clarify_downgrade_defined": "clarification without new evidence becomes `DEBT`" in reviewer,
            "repair_regression_route_defined": "repair-regression` opens the circuit breaker" in skill,
        }
        expect = case["expect"]
        mismatches = {
            key: {"expected": value, "actual": actual.get(key)}
            for key, value in expect.items() if actual.get(key) != value
        }
        return {"passed": not mismatches, "mismatches": mismatches, "actual": actual}

    module = _load_analyzer()
    given = case["input"]
    result = module.analyze(
        given["diff"], graph=given.get("graph"), resolutions=given.get("resolutions"))
    expect = case["expect"]
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
    mismatches = {
        key: {"expected": value, "actual": actual.get(key)}
        for key, value in expect.items() if actual.get(key) != value
    }
    return {"passed": not mismatches, "mismatches": mismatches, "actual": actual}
