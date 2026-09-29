"""pr-loop v4 contract (GW-017): one closed loop per task, two model calls, no rounds.

The loop is the pipeline — implement → gate → probe → independent verify →
one repair → one delta verify → human. It iterates over tasks, never over
rounds inside a task. Task state lives in Backlog.md, read one task at a time.
"""

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PLUGIN = ROOT / "plugin"
SKILL_DIR = PLUGIN / "skills" / "pr-loop"
SCAFFOLD = PLUGIN / "assets" / "scaffold"


class LoopShapeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.skill = (SKILL_DIR / "SKILL.md").read_text()
        cls.reviewer = (PLUGIN / "agents" / "pr-reviewer.md").read_text()

    def test_two_model_calls_and_no_rounds(self):
        self.assertIn("at most two model calls", self.skill)
        self.assertIn("never a third", self.skill)
        for gone in ("circuit breaker", "Convergence mode", "convergence mode",
                     "`clarify`", "round 3", "Round 3"):
            self.assertNotIn(gone, self.skill, gone)

    def test_states_include_probe_between_gate_and_verify(self):
        gate = self.skill.find("## 4. GATE")
        probe = self.skill.find("## 5. PROBE")
        verify = self.skill.find("## 6. VERIFY")
        self.assertTrue(0 <= gate < probe < verify, (gate, probe, verify))

    def test_findings_block_only_with_a_repro(self):
        self.assertIn("A finding without a `repro` never blocks", self.skill)
        self.assertIn('"repro"', self.reviewer)
        self.assertNotIn("0.50", self.reviewer)
        self.assertNotIn("clarif", self.reviewer)
        for question in ("acceptance", "drift", "wrong output"):
            self.assertIn(question, self.reviewer)

    def test_prose_and_document_claims_never_block(self):
        self.assertIn("prose", self.skill)
        self.assertRegex(self.skill, r"(?i)prose[^.\n]*never blocks")

    def test_repair_happens_once(self):
        self.assertIn("## 7. REPAIR (once)", self.skill)
        self.assertIn("## 8. RE-VERIFY (model call 2, delta only)", self.skill)
        self.assertIn("Decision: not met", self.skill)


class TaskStoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.skill = (SKILL_DIR / "SKILL.md").read_text()
        cls.init = (PLUGIN / "skills" / "groundwork-init" / "SKILL.md").read_text()

    def test_spec_reads_one_task_through_backlog(self):
        self.assertIn("backlog task list --ready --plain", self.skill)
        self.assertIn("backlog task view <id> --plain", self.skill)
        self.assertIn("Read nothing else", self.skill)
        for gone in ("ready.py", "tasks/TODO.md", "DONE.md", "housekeeping"):
            self.assertNotIn(gone, self.skill, gone)

    def test_task_must_declare_a_probe_or_is_not_eligible(self):
        self.assertIn("Probe:", self.skill)
        self.assertIn("not eligible", self.skill)

    def test_debt_is_one_draft_line_with_a_case_or_run_id(self):
        self.assertIn("--draft", self.skill)
        self.assertRegex(self.skill, r"case <id>|run <id>")
        self.assertNotIn("fully-specified", self.skill)

    def test_ready_script_and_scaffold_todo_are_gone(self):
        self.assertFalse((SKILL_DIR / "scripts" / "ready.py").exists())
        self.assertFalse((SCAFFOLD / "tasks").exists())
        self.assertIn("backlog init", self.init)
        self.assertIn("## Upgrading a repo initialized before 0.6", self.init)
        for step in ("migrate_todo.py", "tasks/TODO.md", ".githooks/commit-msg", ".groundwork-version"):
            self.assertIn(step, self.init.split("## Upgrading a repo initialized before 0.6")[1], step)


class EvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.skill = (SKILL_DIR / "SKILL.md").read_text()

    def test_pr_body_is_the_six_section_template(self):
        for heading in ("## Why", "## What changed", "## Verification",
                        "## Problems found", "## Follow-ups", "## Reviewer notes"):
            self.assertIn(heading, self.skill, heading)
        self.assertIn("Task (verbatim)", self.skill)
        self.assertIn("pr_check.py", self.skill)

    def test_one_review_artifact_per_pr(self):
        self.assertIn("tasks/reviews/pr<N>.json", self.skill)
        self.assertNotIn("-resolution.json", self.skill)
        self.assertNotIn("-verification.json", self.skill)

    def test_ledger_caps_review_calls_at_two(self):
        self.assertIn('"review_calls":2', self.skill)
        self.assertNotIn('"converged"', self.skill)
        self.assertNotIn('"escalations"', self.skill)


class DecisionRecordTests(unittest.TestCase):
    def test_gw017_justifies_the_loop_name_and_is_indexed(self):
        adr = ROOT / "docs" / "decisions" / "GW-017-pr-loop-v4-one-loop-two-calls.md"
        self.assertTrue(adr.exists())
        text = adr.read_text()
        self.assertIn("loop engineering", text)
        self.assertIn("self-supervised", text)
        self.assertRegex(text, re.compile(r"^Status: accepted", re.M))
        index = (ROOT / "docs" / "decisions" / "INDEX.md").read_text()
        self.assertIn("GW-017", index)
        reference = (ROOT / "docs" / "groundwork.md").read_text()
        self.assertIn("backlog task list --ready", reference)
        self.assertNotIn("circuit breaker", reference)


if __name__ == "__main__":
    unittest.main()


class PrStatusConfiguredTests(unittest.TestCase):
    """TASK-1: pr-loop sets status PR, so groundwork-init must configure it."""

    @classmethod
    def setUpClass(cls):
        cls.loop = (SKILL_DIR / "SKILL.md").read_text()
        cls.init = (PLUGIN / "skills" / "groundwork-init" / "SKILL.md").read_text()
        cls.step = re.search(r"\n2\. \*\*Task store\.\*\*.*?\n\n3\. ", cls.init, re.S).group(0)

    def test_init_task_store_step_adds_pr_status_additively(self):
        self.assertIn("backlog/config.yml", self.step)
        self.assertIn("`PR`", self.step)
        self.assertIn("between In Progress and Done", self.step)
        self.assertIn("keeps", self.step)
        self.assertIn("once", self.step)

    def test_loop_and_init_name_the_same_status(self):
        status = re.search(r"backlog task edit <id> -s (\S+?)`", self.loop).group(1)
        self.assertIn(f"`{status}`", self.step)
