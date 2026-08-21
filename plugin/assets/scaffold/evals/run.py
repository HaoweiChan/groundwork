#!/usr/bin/env python3
"""Task-agnostic groundwork eval runner."""
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
    try:
        sha = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
            capture_output=True, text=True, check=True).stdout.strip()
        dirty = bool(subprocess.run(
            ["git", "status", "--porcelain", "--", ".",
             ":(exclude)evals/report/history.jsonl"], cwd=ROOT,
            capture_output=True, text=True, check=True).stdout.strip())
        return sha, dirty
    except Exception:
        return None, False


def load_cases(suite):
    cases = []
    for directory in CASE_DIRS:
        for path in sorted(directory.rglob("*.json")):
            case = json.loads(path.read_text())
            case["_file"] = str(path.relative_to(ROOT))
            case["_kind"] = directory.name
            if suite == "all" or suite in case.get("suites", ["fast"]):
                cases.append(case)
    return cases


def run_case(case):
    started = time.monotonic()
    try:
        module = importlib.import_module(f"src.{case['task']}.eval_adapter")
        result = module.run_case(case)
    except Exception:
        result = {"passed": False, "error": traceback.format_exc(limit=3)}
    result.setdefault("passed", False)
    result["seconds"] = round(time.monotonic() - started, 2)
    result["id"] = case.get("id", case["_file"])
    result["kind"] = case["_kind"]
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite", default="fast")
    parser.add_argument("--baseline", default=str(BASELINE))
    parser.add_argument("--update-baseline", action="store_true")
    parser.add_argument("--report", action="store_true")
    parser.add_argument("--no-report", action="store_true")
    args = parser.parse_args()

    started = time.monotonic()
    sys.path.insert(0, str(ROOT))
    cases = load_cases(args.suite)
    results = [run_case(case) for case in cases]
    total = len(results)
    passed = sum(result["passed"] for result in results)
    score = passed / total if total else 1.0

    if not cases:
        print(f"[eval] suite '{args.suite}': no cases yet — nothing to gate on.")
    for result in results:
        mark = "PASS" if result["passed"] else "FAIL"
        print(f"[{mark}] {result['id']} ({result['kind']}, {result['seconds']}s)")
        if not result["passed"] and "error" in result:
            print(f"       {result['error'].strip().splitlines()[-1]}")
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
        costs = [result["cost_usd"] for result in results
                 if result.get("cost_usd") is not None]
        sha, dirty = git_info()
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        with HISTORY.open("a") as history:
            history.write(json.dumps({
                "ts": time.strftime("%Y%m%d-%H%M%S"),
                "suite": args.suite,
                "sha": sha,
                "dirty": dirty,
                "passed": passed,
                "total": total,
                "score": round(score, 4),
                "wall_s": round(time.monotonic() - started, 2),
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
        print("[eval] INVARIANT VIOLATION: invariants require 100%", file=sys.stderr)
        return 1
    if args.suite in baseline and score < baseline[args.suite]:
        print(f"[eval] REGRESSION: {score:.3f} < {baseline[args.suite]:.3f}",
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
