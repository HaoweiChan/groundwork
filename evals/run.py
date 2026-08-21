#!/usr/bin/env python3
"""Task-agnostic eval runner.

Case contract (one JSON file per case, under evals/golden/ or evals/adversarial/):

    {
      "id": "unique-case-id",
      "task": "sec10k",                  # -> src/<task>/eval_adapter.py
      "suites": ["fast", "invariant"],   # default ["fast"]
      "input": { ... },                  # task-defined
      "expect": { ... }                  # task-defined
    }

Each task implements src/<task>/eval_adapter.py with:

    def run_case(case: dict) -> dict    # {"passed": bool, ...anything else}

The runner owns: discovery, suite filtering, scoring, baseline gating,
report history. Adapters own: how to run a case and judge it.

Report policy: every run appends one line to evals/report/history.jsonl.
A full per-case report is written only on --report, --suite all, or a red
run (a failed case or a score below baseline) — see docs/decisions/GW-008.
"""
import argparse
import importlib
import json
import subprocess
import sys
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CASE_DIRS = [ROOT / "evals" / "golden", ROOT / "evals" / "adversarial"]
BASELINE = ROOT / ".eval-baseline.json"
REPORT_DIR = ROOT / "evals" / "report"
HISTORY = REPORT_DIR / "history.jsonl"


def git_info():
    """(short sha, dirty) or (None, False) if git is unavailable."""
    try:
        sha = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
            capture_output=True, text=True, check=True).stdout.strip()
        dirty = bool(subprocess.run(
            ["git", "status", "--porcelain"], cwd=ROOT,
            capture_output=True, text=True, check=True).stdout.strip())
        return sha, dirty
    except Exception:
        return None, False


def load_cases(suite):
    cases = []
    for d in CASE_DIRS:
        for f in sorted(d.rglob("*.json")):
            case = json.loads(f.read_text())
            case["_file"] = str(f.relative_to(ROOT))
            case["_kind"] = d.name  # golden | adversarial
            if suite == "all" or suite in case.get("suites", ["fast"]):
                cases.append(case)
    return cases


def run_case(case):
    t0 = time.monotonic()
    try:
        mod = importlib.import_module(f"src.{case['task']}.eval_adapter")
        result = mod.run_case(case)
    except Exception:
        result = {"passed": False, "error": traceback.format_exc(limit=3)}
    result.setdefault("passed", False)
    result["seconds"] = round(time.monotonic() - t0, 2)
    result["id"] = case.get("id", case["_file"])
    result["kind"] = case["_kind"]
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--suite", default="fast")
    ap.add_argument("--baseline", default=str(BASELINE))
    ap.add_argument("--update-baseline", action="store_true")
    ap.add_argument("--report", action="store_true", help="force a full per-case report")
    ap.add_argument("--no-report", action="store_true",
                     help="hard off switch: no history line, no full report "
                          "(for high-frequency callers like the post-edit hook)")
    args = ap.parse_args()

    t0 = time.monotonic()
    sys.path.insert(0, str(ROOT))
    cases = load_cases(args.suite)
    results = [run_case(c) for c in cases] if cases else []
    total = len(results)
    passed = sum(r["passed"] for r in results)
    score = passed / total if total else 1.0

    if not cases:
        print(f"[eval] suite '{args.suite}': no cases yet — nothing to gate on. "
              "Add cases under evals/golden/ or evals/adversarial/.")
    for r in results:
        mark = "PASS" if r["passed"] else "FAIL"
        print(f"[{mark}] {r['id']} ({r['kind']}, {r['seconds']}s)")
        if not r["passed"] and "error" in r:
            print(f"       {r['error'].strip().splitlines()[-1]}")
    if cases:
        print(f"[eval] suite '{args.suite}': {passed}/{total} = {score:.3f}")

    baseline_path = Path(args.baseline)
    baseline = json.loads(baseline_path.read_text()) if baseline_path.exists() else {}
    red = total > 0 and (passed < total or
                          (args.suite in baseline and score < baseline[args.suite]))

    report_name = None
    if not args.no_report and (args.report or args.suite == "all" or red):
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        stamp = time.strftime("%Y%m%d-%H%M%S")
        report_name = f"{stamp}-{args.suite}.json"
        (REPORT_DIR / report_name).write_text(json.dumps(
            {"suite": args.suite, "score": score, "results": results}, indent=2))

    if not args.no_report:
        costs = [r["cost_usd"] for r in results if r.get("cost_usd") is not None]
        sha, dirty = git_info()
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        with HISTORY.open("a") as f:
            f.write(json.dumps({
                "ts": time.strftime("%Y%m%d-%H%M%S"),
                "suite": args.suite,
                "sha": sha,
                "dirty": dirty,
                "passed": passed,
                "total": total,
                "score": round(score, 4),
                "wall_s": round(time.monotonic() - t0, 2),
                "cost_usd": round(sum(costs), 4) if costs else None,
                "report": report_name,
            }) + "\n")

    if args.update_baseline:
        baseline[args.suite] = score
        baseline_path.write_text(json.dumps(baseline, indent=2) + "\n")
        print(f"[eval] baseline['{args.suite}'] = {score:.3f} (recorded)")
        return 0
    if not cases:
        return 0
    if args.suite == "invariant" and passed < total:
        print("[eval] INVARIANT VIOLATION: invariants are absolute, 100% required",
              file=sys.stderr)
        return 1
    if args.suite in baseline and score < baseline[args.suite]:
        print(f"[eval] REGRESSION: {score:.3f} < baseline {baseline[args.suite]:.3f}",
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
