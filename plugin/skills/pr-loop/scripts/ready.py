#!/usr/bin/env python3
"""Task board for pr-loop: every block with status, priority, and dependencies.

Lives in the groundwork plugin; resolve this script from the installed pr-loop
skill directory and run it from the target repo's root:
  python3 <pr-loop-skill-dir>/scripts/ready.py [--selftest]
Reads tasks/TODO.md (Queue/Debt) and tasks/DONE.md (one-liners) in the CWD.

Output is one line per block, grouped by section: state, id, priority, title,
and every dependency with its own satisfaction mark (task-master style):
  ready       M9         P2  Cost/model ablation
  blocked     M10        P2  A-Freeze | deps: M9(x) M12(x)
States: ready | blocked | in-progress | pr | parked (Debt). Ready rows sort by
(priority, id); a block with no `Priority:` line defaults to P2.

ponytail: line-regex parser over the block format the pr-loop skill defines,
not a markdown parser — upgrade only if the format ever outgrows it.
"""
import pathlib
import re
import sys

TODO = pathlib.Path("tasks/TODO.md")
DONE = pathlib.Path("tasks/DONE.md")
# ids like M9, T3, T-R89, T-M42-20-D1: uppercase start, must contain a digit
ID = r"[A-Z][A-Za-z0-9-]*\d[A-Za-z0-9-]*"
DONE_LINE = re.compile(rf"^[-*]\s*({ID})\s+—")
HEAD = re.compile(rf"^#{{2,3}}\s+({ID})\s+—\s+(.*?)\s*\[status:\s*([a-z-]+)\]")
DEPS = re.compile(r"^Depends:\s*(.+)")
PRIORITY = re.compile(r"^Priority:\s*(P\d+)")
DEFAULT_PRIORITY = "P2"


def parse(text):
    tasks, cur, section = {}, None, ""
    for line in text.splitlines():
        if line.startswith("## "):
            section, cur = line[3:].strip().lower(), None
        elif m := HEAD.match(line):
            cur = m.group(1)
            tasks[cur] = {
                "title": m.group(2).strip(),
                "status": m.group(3),
                "deps": [],
                "section": section,
                "priority": DEFAULT_PRIORITY,
            }
        elif cur and (m := DEPS.match(line)):
            tasks[cur]["deps"] = re.findall(ID, m.group(1))
        elif cur and (m := PRIORITY.match(line)):
            tasks[cur]["priority"] = m.group(1)
    return tasks


def done_ids(text):
    return {m.group(1) for line in text.splitlines() if (m := DONE_LINE.match(line))}


def row(state, tid, t, done):
    deps = ""
    if t["deps"]:
        deps = " | deps: " + " ".join(
            f"{d}({'v' if done(d) else 'x'})" for d in t["deps"])
    title = t["title"][:48]
    return f"{state:<12}{tid:<14}{t['priority']}  {title}{deps}"


def main():
    tasks = parse(TODO.read_text())
    finished = done_ids(DONE.read_text()) if DONE.exists() else set()
    if not tasks:
        print("no tasks found in tasks/TODO.md")
        return
    is_done = lambda d: d in finished or tasks.get(d, {}).get("status") == "done"

    for section in ("queue", "debt"):
        blocks = [(tid, t) for tid, t in tasks.items() if t["section"] == section]
        if not blocks:
            continue
        print(f"## {section.capitalize()}")
        ready, rest = [], []
        for tid, t in blocks:
            if section == "debt":
                rest.append(("parked", tid, t))
            elif t["status"] != "todo":
                rest.append((t["status"], tid, t))
            elif all(is_done(d) for d in t["deps"]):
                ready.append((t["priority"], tid, t))
            else:
                rest.append(("blocked", tid, t))
        for pr_, tid, t in sorted(ready):
            print(row("ready", tid, t, is_done))
        for state, tid, t in sorted(rest, key=lambda r: (r[2]["priority"], r[1])):
            print(row(state, tid, t, is_done))


def selftest():
    t = parse(
        "## Queue\n"
        "### T1 — a [status: done]\n"
        "### T2 — b [status: todo]\nDepends: T1\n"
        "### T3 — c [status: todo]\nDepends: T2, T9\n"
        "### T4 — d [status: in-progress]\n"
        "### M8 — e [status: todo]\nDepends: T1\n"
        "### T-M42-20 — compound id [status: pr]\n"
        "### T-M42-20-D1 — child [status: todo]\nDepends: T-M42-20\n"
    )
    assert t["T1"]["status"] == "done" and t["T2"]["deps"] == ["T1"]
    assert t["T2"]["title"] == "b"
    assert t["T-M42-20"]["status"] == "pr"
    # compound ids parse whole, never as an embedded M42
    assert t["T-M42-20-D1"]["deps"] == ["T-M42-20"]
    assert [d for d in t["T3"]["deps"] if t.get(d, {}).get("status") != "done"] == ["T2", "T9"]
    assert t["M8"]["deps"] == ["T1"]
    assert t["T2"]["priority"] == DEFAULT_PRIORITY
    t2 = parse("## Queue\n### T1 — a [status: todo]\n## Debt\n### T2 — b [status: todo]\n")
    assert t2["T1"]["section"] == "queue" and t2["T2"]["section"] == "debt"
    assert done_ids("# Done\n- M8 — title (2026-08-20) — x\n- T-M40-1 — y (d) — z\n") == {"M8", "T-M40-1"}

    p = parse(
        "## Queue\n"
        "### T9 — low [status: todo]\nPriority: P3\n"
        "### T1 — high [status: todo]\nPriority: P1\n"
        "### T5 — high-b [status: todo]\nPriority: P1\n"
        "### T2 — default [status: todo]\n"
    )
    assert [p[t_]["priority"] for t_ in ("T9", "T1", "T5", "T2")] == ["P3", "P1", "P1", "P2"]
    assert sorted((p[t_]["priority"], t_) for t_ in p) == [
        ("P1", "T1"), ("P1", "T5"), ("P2", "T2"), ("P3", "T9")]
    print("selftest ok")


if __name__ == "__main__":
    selftest() if "--selftest" in sys.argv else main()
