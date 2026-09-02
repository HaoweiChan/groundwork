#!/usr/bin/env python3
"""One-off: turn tasks/TODO.md blocks into `backlog task create` commands (GW-017).

  python3 migrate_todo.py [tasks/TODO.md]        # print the commands (dry run)
  python3 migrate_todo.py tasks/TODO.md --run    # execute them in the CWD

Only `[status: todo]` blocks move: Queue blocks become tasks, Debt blocks become
drafts. pr/in-progress/done blocks are in flight or finished and stay in git
history. Old ids survive as `--ref`. Set BACKLOG="npx -y backlog.md" when the CLI is
not installed. Stdlib only.

ponytail: line-regex parser over the retired TODO.md block format; it exists
only to migrate, not to keep that format alive.
"""
import os
import re
import shlex
import subprocess
import sys

ID = r"[A-Z][A-Za-z0-9]*(?:-[A-Za-z0-9]+)+|[A-Z][A-Za-z0-9]*\d[A-Za-z0-9]*"
HEAD = re.compile(rf"^#{{2,3}}\s+({ID})\s+—\s+(.*?)\s*\[status:\s*([a-z-]+)\]", re.M)
SECTION = re.compile(r"^## (.+?)\s*$", re.M)
FIELD = re.compile(r"^([A-Z][A-Za-z ]+):\s*(.*)$")
PRIORITY = {"P1": "high", "P2": "medium", "P3": "low"}


def backlog_bin(env):
    """`BACKLOG="npx -y backlog.md"` when the CLI is not on PATH."""
    return shlex.split(env.get("BACKLOG") or "backlog")


def blocks(text):
    """Yield (section, id, title, status, fields) for every block."""
    section = ""
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        sec = SECTION.match(line)
        if sec:
            section = sec.group(1); i += 1; continue
        head = HEAD.match(line)
        if not head:
            i += 1; continue
        fields, key = {}, None
        i += 1
        while i < len(lines) and not HEAD.match(lines[i]) and not SECTION.match(lines[i]):
            m = FIELD.match(lines[i])
            if m:
                key = m.group(1); fields[key] = m.group(2).strip()
            elif key and lines[i].strip():
                fields[key] = (fields[key] + " " + lines[i].strip()).strip()
            i += 1
        yield section, head.group(1), head.group(2), head.group(3), fields


def commands(text, env=None):
    bin_ = backlog_bin(os.environ if env is None else env)
    out = []
    for section, tid, title, status, f in blocks(text):
        if status != "todo":
            continue
        debt = section.lower().startswith("debt")
        desc = f.get("Spec", "").strip() or title
        if f.get("Depends"):  # old ids do not exist in Backlog.md; keep them readable, not as --dep
            desc += f"\n\nDepends (TODO.md ids): {f['Depends'].strip()}"
        desc += "\n\nProbe: none — migrated from TODO.md"
        cmd = bin_ + ["task", "create", title, "-d", desc,
               "--ref", f.get("Origin") or f"TODO.md {tid}"]
        if f.get("Acceptance"):
            cmd += ["--ac", f["Acceptance"]]
        if f.get("Priority") in PRIORITY:
            cmd += ["--priority", PRIORITY[f["Priority"]]]
        if debt:
            cmd += ["--draft", "-l", "debt"]
        out.append(cmd)
    return out


def render(cmds):
    return [shlex.join(c) for c in cmds]


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    run = "--run" in argv
    argv = [a for a in argv if a != "--run"]
    path = argv[0] if argv else "tasks/TODO.md"
    with open(path, encoding="utf-8") as fh:
        cmds = commands(fh.read())
    if not run:
        print("\n".join(render(cmds)))
        return 0
    for c in cmds:
        subprocess.run(c, check=True)
    print(f"migrated {len(cmds)} block(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
