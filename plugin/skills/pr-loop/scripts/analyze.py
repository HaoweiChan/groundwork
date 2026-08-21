#!/usr/bin/env python3
"""Build a compact, deterministic review-planning packet from a git diff.

The analyzer deliberately does not call Graphify or any model. It consumes an
existing graph when available and otherwise reports changed-file evidence only.
"""
import argparse
import json
import shlex
import subprocess
import sys
from pathlib import Path


SOURCE_SUFFIXES = {
    ".c", ".cc", ".cpp", ".cs", ".go", ".h", ".hpp", ".java", ".js",
    ".jsx", ".kt", ".kts", ".m", ".php", ".py", ".rb", ".rs", ".swift",
    ".ts", ".tsx",
}
DEPENDENCY_FILES = {
    "build.gradle", "build.gradle.kts", "cargo.toml", "composer.json",
    "gemfile", "go.mod", "mix.exs", "package.json", "package-lock.json",
    "package.swift", "pipfile", "pipfile.lock", "pnpm-lock.yaml", "podfile",
    "poetry.lock", "pom.xml", "pyproject.toml", "requirements.txt", "uv.lock",
    "yarn.lock",
}
HIGH_RISK_PARTS = {
    "api", "auth", "migration", "migrations", "openapi", "payments",
    "permissions", "schema", "security",
}
RISK_ORDER = {"low": 0, "medium": 1, "high": 2}


def _unique(items):
    return list(dict.fromkeys(items))


def _diff_path(line):
    """Return the destination path from a `diff --git` header."""
    try:
        parts = shlex.split(line)
    except ValueError:
        parts = line.split()
    if len(parts) < 4:
        return None
    path = parts[3]
    path = path[2:] if path.startswith("b/") else path
    return _decode_git_path(path)


def _decode_git_path(path):
    """Decode Git's C-style octal quoting into a filesystem path."""
    if "\\" not in path:
        return path
    escapes = {
        "a": 7, "b": 8, "t": 9, "n": 10, "v": 11, "f": 12, "r": 13,
        '"': 34, "\\": 92,
    }
    raw = bytearray()
    index = 0
    while index < len(path):
        char = path[index]
        if char != "\\":
            raw.extend(char.encode("utf-8"))
            index += 1
            continue
        octal = path[index + 1:index + 4]
        if len(octal) == 3 and all(digit in "01234567" for digit in octal):
            raw.append(int(octal, 8))
            index += 4
            continue
        following = path[index + 1:index + 2]
        if following in escapes:
            raw.append(escapes[following])
            index += 2
            continue
        raw.append(ord("\\"))
        index += 1
    return raw.decode("utf-8", "surrogateescape")


def parse_diff(diff_text):
    files = []
    added_files = []
    deleted_files = []
    lines_added = 0
    lines_deleted = 0
    current = None
    in_hunk = False

    for line in diff_text.splitlines():
        if line.startswith("diff --git "):
            current = _diff_path(line)
            if current:
                files.append(current)
            in_hunk = False
        elif line.startswith("new file mode ") and current:
            added_files.append(current)
        elif line.startswith("deleted file mode ") and current:
            deleted_files.append(current)
        elif line.startswith("@@"):
            in_hunk = True
        elif in_hunk and line.startswith("+") and not line.startswith("+++"):
            lines_added += 1
        elif in_hunk and line.startswith("-") and not line.startswith("---"):
            lines_deleted += 1

    return {
        "files": _unique(files),
        "added_files": _unique(added_files),
        "deleted_files": _unique(deleted_files),
        "lines_added": lines_added,
        "lines_deleted": lines_deleted,
    }


def _is_source(path):
    return Path(path).suffix.lower() in SOURCE_SUFFIXES


def _is_dependency_file(path):
    name = Path(path).name.lower()
    return name in DEPENDENCY_FILES or name.startswith("requirements") and name.endswith(".txt")


def build_preflight(change, resolutions=None):
    questions = []
    new_sources = [path for path in change["added_files"] if _is_source(path)]
    dependency_files = [path for path in change["files"] if _is_dependency_file(path)]
    if new_sources:
        questions.append({
            "id": "new-source-surface",
            "files": new_sources,
            "resolve": "reuse existing code or justify why each new file/abstraction is required",
        })
    if dependency_files:
        questions.append({
            "id": "dependency-change",
            "files": dependency_files,
            "resolve": "use the standard library/existing dependency or justify the added dependency",
        })
    resolutions = resolutions if isinstance(resolutions, dict) else {}
    accepted = {}
    unresolved_files = []
    for question in questions:
        resolution = resolutions.get(question["id"])
        per_file = resolution.get("files", {}) if isinstance(resolution, dict) else {}
        if len(question["files"]) == 1 and isinstance(resolution, dict) and not per_file:
            per_file = {question["files"][0]: resolution}
        accepted_files = {}
        for path in question["files"]:
            item = per_file.get(path) if isinstance(per_file, dict) else None
            if (isinstance(item, dict)
                    and item.get("outcome") in {"reused", "justified"}
                    and str(item.get("reason", "")).strip()):
                accepted_files[path] = item
            else:
                unresolved_files.append(path)
        if len(accepted_files) == len(question["files"]):
            accepted[question["id"]] = {"files": accepted_files}
    unresolved = [question["id"] for question in questions if question["id"] not in accepted]
    return {
        "status": "resolve" if unresolved else "pass",
        "questions": questions,
        "resolutions": accepted,
        "unresolved_ids": unresolved,
        "unresolved_files": unresolved_files,
    }


def classify_risk(change, preflight):
    reasons = []
    level = "low"

    def add(reason, severity):
        nonlocal level
        reasons.append(reason)
        if RISK_ORDER[severity] > RISK_ORDER[level]:
            level = severity

    parts = {
        token
        for path in change["files"]
        for part in Path(path).parts
        for token in (part.lower(), Path(part).stem.lower())
    }
    if any(item["id"] == "dependency-change" for item in preflight["questions"]):
        add("dependency-change", "high")
    if parts & HIGH_RISK_PARTS:
        add("sensitive-boundary", "high")
    if len(change["files"]) > 10 or change["lines_added"] + change["lines_deleted"] > 500:
        add("large-change-surface", "high")
    if change["deleted_files"]:
        add("deleted-files", "medium")
    if any(item["id"] == "new-source-surface" for item in preflight["questions"]):
        add("new-source-surface", "medium")

    production_changed = any(path.startswith("src/") and _is_source(path) for path in change["files"])
    eval_changed = any(path.startswith(("evals/", "test/", "tests/")) for path in change["files"])
    if production_changed and not eval_changed:
        add("behavior-without-eval-diff", "medium")

    return {"level": level, "reasons": _unique(reasons)}


def graph_impact(change, graph, max_nodes=20):
    empty = {
        "source": "changed-files",
        "changed_nodes": [],
        "affected_nodes": [],
        "affected_files": [],
    }
    if not isinstance(graph, dict):
        return empty

    nodes = {node.get("id"): node for node in graph.get("nodes", []) if node.get("id")}
    if not nodes:
        return empty
    changed_paths = set(change["files"])
    changed_nodes = sorted(
        node_id for node_id, node in nodes.items()
        if node.get("source_file") in changed_paths
    )
    if not changed_nodes:
        return {
            "source": "graphify",
            "changed_nodes": [],
            "affected_nodes": [],
            "affected_files": [],
        }

    changed_set = set(changed_nodes)
    neighbors = set()
    for edge in graph.get("edges", []):
        source, target = edge.get("source"), edge.get("target")
        if source in changed_set and target in nodes and target not in changed_set:
            neighbors.add(target)
        if target in changed_set and source in nodes and source not in changed_set:
            neighbors.add(source)
    affected_nodes = sorted(neighbors)[:max_nodes]
    affected_files = sorted({
        nodes[node_id].get("source_file") for node_id in affected_nodes
        if nodes[node_id].get("source_file")
    })
    return {
        "source": "graphify",
        "changed_nodes": changed_nodes,
        "affected_nodes": affected_nodes,
        "affected_files": affected_files,
    }


def build_review(change, risk, preflight, impact):
    targets = ["task-acceptance", "repo-invariants"]
    if "behavior-without-eval-diff" in risk["reasons"]:
        targets.append("missing-behavior-case")
    if preflight["questions"]:
        targets.append("preflight-resolutions")
    if impact["affected_nodes"]:
        targets.append("graphify-impact")
    if "sensitive-boundary" in risk["reasons"]:
        targets.append("boundary-compatibility")

    context_files = _unique(change["files"] + impact["affected_files"])
    return {
        "mode": "full" if risk["level"] == "high" else "focused",
        "targets": targets,
        "context_files": context_files,
    }


def analyze(diff_text, graph=None, max_impact_nodes=20, resolutions=None):
    change = parse_diff(diff_text)
    preflight = build_preflight(change, resolutions)
    risk = classify_risk(change, preflight)
    impact = graph_impact(change, graph, max_nodes=max_impact_nodes)
    return {
        "version": 1,
        "change": change,
        "risk": risk,
        "preflight": preflight,
        "impact": impact,
        "review": build_review(change, risk, preflight, impact),
    }


def _git_diff(repo, base, head):
    proc = subprocess.run(
        ["git", "diff", "--find-renames", "--unified=0", f"{base}...{head}"],
        cwd=repo, capture_output=True, text=True,
    )
    if proc.returncode:
        raise RuntimeError(proc.stderr.strip() or "git diff failed")
    return proc.stdout


def _load_graph(path):
    if path is None or not path.is_file():
        return None
    return json.loads(path.read_text())


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--base", help="base revision for a three-dot git diff")
    source.add_argument("--diff-file", type=Path, help="read a unified diff from this file")
    parser.add_argument("--head", default="HEAD")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--graph", type=Path, default=Path("graphify-out/graph.json"))
    parser.add_argument("--max-impact-nodes", type=int, default=20)
    parser.add_argument("--resolutions", type=Path,
                        help="JSON object keyed by preflight question id")
    parser.add_argument("--require-preflight", action="store_true",
                        help="exit 3 while a Ponytail question is unresolved")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)

    try:
        diff_text = args.diff_file.read_text() if args.diff_file else _git_diff(args.repo, args.base, args.head)
        graph_path = args.graph if args.graph.is_absolute() else args.repo / args.graph
        resolutions = json.loads(args.resolutions.read_text()) if args.resolutions else None
        packet = analyze(diff_text, _load_graph(graph_path), args.max_impact_nodes, resolutions)
    except (OSError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"pr-loop analyze: {exc}", file=sys.stderr)
        return 2

    rendered = json.dumps(packet, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered)
    else:
        sys.stdout.write(rendered)
    if args.require_preflight and packet["preflight"]["status"] != "pass":
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
