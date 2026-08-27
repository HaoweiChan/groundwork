#!/usr/bin/env python3
"""List pr-loop tasks that are ready to run (status todo, all Depends done).

Lives in the groundwork plugin; resolve this script from the installed pr-loop
skill directory and run it from the target repo's root:
  python3 <pr-loop-skill-dir>/scripts/ready.py [--selftest]
Reads tasks/TODO.md (Queue/Debt) and tasks/DONE.md (one-liners) in the CWD.
Ready tasks print sorted by (priority, id); a block with no `Priority:` line
defaults to P2.

ponytail: line-regex parser over the block format the pr-loop skill defines,
not a markdown parser — upgrade only if the format ever outgrows it.
"""
import pathlib
import re
import sys

TODO = pathlib.Path("tasks/TODO.md")
DONE = pathlib.Path("tasks/DONE.md")
DONE_LINE = re.compile(r"^[-*]\s*([A-Z]+\d+)\s+—")
HEAD = re.compile(r"^#{2,3}\s+([A-Z]+\d+)\s+—.*\[status:\s*([a-z-]+)\]")
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
                "status": m.group(2),
                "deps": [],
                "section": section,
                "priority": DEFAULT_PRIORITY,
            }
        elif cur and (m := DEPS.match(line)):
            tasks[cur]["deps"] = re.findall(r"[A-Z]+\d+", m.group(1))
        elif cur and (m := PRIORITY.match(line)):
            tasks[cur]["priority"] = m.group(1)
    return tasks


def done_ids(text):
    return {m.group(1) for line in text.splitlines() if (m := DONE_LINE.match(line))}


def main():
    tasks = parse(TODO.read_text())
    for tid in done_ids(DONE.read_text()) if DONE.exists() else ():
        tasks.setdefault(
            tid, {"status": "done", "deps": [], "section": "done", "priority": DEFAULT_PRIORITY}
        )
    if not tasks:
        print("no tasks found in tasks/TODO.md")
        return
    ready = []
    for tid, t in tasks.items():
        # ponytail: only Queue blocks are candidates — Debt is parked by definition
        if t["status"] != "todo" or t["section"] != "queue":
            continue
        missing = [d for d in t["deps"] if tasks.get(d, {}).get("status") != "done"]
        if missing:
            print(f"blocked {tid}  needs {', '.join(missing)}")
        else:
            ready.append((t["priority"], tid))
    for priority, tid in sorted(ready):
        print(f"ready   {tid}   [{priority}]")


def selftest():
    t = parse(
        "## Queue\n"
        "### T1 — a [status: done]\n"
        "### T2 — b [status: todo]\nDepends: T1\n"
        "### T3 — c [status: todo]\nDepends: T2, T9\n"
        "### T4 — d [status: in-progress]\n"
        "### M8 — e [status: todo]\nDepends: T1\n"
    )
    assert t["T1"]["status"] == "done" and t["T2"]["deps"] == ["T1"]
    assert [d for d in t["T2"]["deps"] if t.get(d, {}).get("status") != "done"] == []
    assert [d for d in t["T3"]["deps"] if t.get(d, {}).get("status") != "done"] == ["T2", "T9"]
    assert t["T4"]["status"] == "in-progress"
    assert t["M8"]["deps"] == ["T1"]
    assert t["T2"]["priority"] == DEFAULT_PRIORITY  # no Priority: line -> default
    t2 = parse("## Queue\n### T1 — a [status: todo]\n## Debt\n### T2 — b [status: todo]\n")
    assert t2["T1"]["section"] == "queue" and t2["T2"]["section"] == "debt"
    assert done_ids("# Done\n- M8 — title (2026-08-20) — ADR-009, PR #12\n- T5 — x\n") == {"M8", "T5"}

    # priority parse + sort: lower P-number ready first, ties broken by id
    p = parse(
        "## Queue\n"
        "### T9 — low [status: todo]\nPriority: P3\n"
        "### T1 — high [status: todo]\nPriority: P1\n"
        "### T5 — high-b [status: todo]\nPriority: P1\n"
        "### T2 — default [status: todo]\n"
    )
    assert [p[t]["priority"] for t in ("T9", "T1", "T5", "T2")] == ["P3", "P1", "P1", "P2"]
    ready_order = sorted((p[t]["priority"], t) for t in p)
    assert ready_order == [("P1", "T1"), ("P1", "T5"), ("P2", "T2"), ("P3", "T9")]
    print("selftest ok")


if __name__ == "__main__":
    selftest() if "--selftest" in sys.argv else main()
