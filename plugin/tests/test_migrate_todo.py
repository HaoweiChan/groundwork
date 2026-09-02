"""tasks/TODO.md blocks → `backlog task create` commands (one-off migration, GW-017)."""

import importlib.util
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "plugin" / "skills" / "groundwork-init" / "scripts" / "migrate_todo.py"

TODO = textwrap.dedent("""
    # Tasks

    ## Queue

    ### M52 — live finance promotion campaign            [status: todo]
    Depends: M51
    Priority: P1
    Spec: run a new, separately authorized journalled campaign for the six
    finance workflows.
    Acceptance: zero wrong-success; each workflow 3/3 on the first pass.

    ### M51 — centralize model policy [status: pr]
    Spec: done already.
    Acceptance: n/a.

    ## Debt

    ### T-M39-15-D2 — two clean branches collide            [status: todo]
    Origin: T-M39-15, cross-branch near-miss 2026-08-28
    Priority: P2
    Spec: in-tree checks cannot see out-of-tree numbers.
    Acceptance: case `task-and-adr-ids-are-unique` covers the cross-branch half.

    ### T-OLD — closed long ago [status: done]
    Spec: gone.
""").lstrip()


def load():
    spec = importlib.util.spec_from_file_location("migrate_todo", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class MigrateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = load()
        cls.cmds = cls.m.commands(TODO)

    def test_queue_todo_becomes_a_task_with_ac_dep_and_priority(self):
        cmd = next(c for c in self.cmds if "live finance promotion campaign" in c[3])
        self.assertEqual(["backlog", "task", "create"], cmd[:3])
        self.assertIn("--priority", cmd); self.assertEqual("high", cmd[cmd.index("--priority") + 1])
        self.assertIn("--dep", cmd); self.assertEqual("M51", cmd[cmd.index("--dep") + 1])
        self.assertIn("--ac", cmd)
        self.assertIn("zero wrong-success; each workflow 3/3 on the first pass.", cmd)
        self.assertIn("--ref", cmd); self.assertEqual("TODO.md M52", cmd[cmd.index("--ref") + 1])
        self.assertNotIn("--draft", cmd)
        desc = cmd[cmd.index("-d") + 1]
        self.assertTrue(desc.startswith("run a new, separately authorized"))
        self.assertIn("Probe: none — migrated from TODO.md", desc)

    def test_debt_todo_becomes_a_draft_with_origin_as_ref(self):
        cmd = next(c for c in self.cmds if "two clean branches collide" in c[3])
        self.assertIn("--draft", cmd)
        self.assertIn("debt", cmd[cmd.index("-l") + 1])
        self.assertIn("T-M39-15, cross-branch near-miss 2026-08-28", cmd)

    def test_done_and_pr_blocks_are_skipped(self):
        titles = [c[3] for c in self.cmds]
        self.assertFalse(any("closed long ago" in t for t in titles))
        self.assertFalse(any("centralize model policy" in t for t in titles))
        self.assertEqual(2, len(self.cmds))

    def test_dry_run_prints_shell_lines(self):
        lines = self.m.render(self.cmds)
        self.assertEqual(2, len(lines))
        self.assertTrue(lines[0].startswith("backlog task create "))
        self.assertIn("'TODO.md M52'", lines[0])


if __name__ == "__main__":
    unittest.main()
