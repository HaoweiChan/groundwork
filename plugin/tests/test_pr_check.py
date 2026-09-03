"""Contract for the PR title/body checker shipped in the scaffold's .github/.

One PR shape for every author (human, Claude, Codex): a typed lowercase title
and a six-section body whose Verification lines are greppable.
"""

import importlib.util
import json
import tempfile
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CHECK = ROOT / "plugin" / "assets" / "scaffold" / ".github" / "pr_check.py"
TEMPLATE = ROOT / "plugin" / "assets" / "scaffold" / ".github" / "PULL_REQUEST_TEMPLATE.md"


def load():
    spec = importlib.util.spec_from_file_location("pr_check", CHECK)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GOOD_BODY = textwrap.dedent("""
    ## Why
    SEC 10-K homepage flow failed live: the planner read the page before the
    async result list rendered (deployed run 69f204dc, failure:locate).

    <details><summary>Task (verbatim): task-12 — settle after async submit</summary>

    > ## Description
    > Observation reads the page before the async result list renders.
    >
    > Probe: run 69f204dc ×1 · $0.01
    >
    > ## Acceptance Criteria
    > - [ ] #1 sec-homepage-async-submit green
    </details>

    ## What changed
    - After a button-driven submit, observation waits for pending fetches to settle.
    Not changed: site-specific selectors.

    ## Verification
    Gate: invariant 122/122 · fast 278/278 · 3f9c1e2
    Red-first: sec-homepage-async-submit watched red at 8a01b77, green at 3f9c1e2
    Live: run 7b2e91aa ×1 on build 3f9c1e2 · $0.01
    Not verified: TAIFEX live

    ## Problems found
    - Normal submits regressed to 30s waits → fast +12s → fixed: settle only when a
      fetch was observed (case form-submit-no-pending-fetch).

    ## Follow-ups
    - TAIFEX live probe on this build (case taifex-homepage-nav)

    ## Reviewer notes
    Start here: src/browser/observe.py settle loop
    Reproduce: python3 -m evals.run --suite fast --case sec-homepage-async-submit
""").lstrip()


class TitleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = load()

    def ok(self, title):
        self.assertEqual([], self.m.check_title(title), title)

    def bad(self, title):
        self.assertTrue(self.m.check_title(title), title)

    def test_typed_lowercase_titles_pass(self):
        self.ok("feat: add homepage showcase")
        self.ok("fix(browser): settle async submits")
        self.ok("chore(tasks): move m43 to done")
        self.ok("docs: refresh readme")

    def test_ids_and_code_spans_may_keep_their_case(self):
        self.ok("fix: close T-M42-4 live clause")
        self.ok("feat: gate access behind `LLM_ACCESS_KEY`")
        self.ok("docs: record ADR-045")

    def test_missing_or_unknown_tag_fails(self):
        self.bad("add homepage showcase")
        self.bad("feature: add homepage showcase")
        self.bad("browser: settle async submits")

    def test_uppercase_anywhere_outside_ids_fails(self):
        self.bad("Feat: add homepage showcase")
        self.bad("feat: Add homepage showcase")
        self.bad("feat: settle SEC submits")

    def test_empty_summary_and_trailing_period_fail(self):
        self.bad("feat:")
        self.bad("feat: ")
        self.bad("feat: add homepage showcase.")


class BodyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = load()

    def errors(self, body):
        return self.m.check_body(body)

    def test_good_body_passes(self):
        self.assertEqual([], self.errors(GOOD_BODY))

    def test_template_itself_fails_until_filled(self):
        self.assertTrue(self.errors(TEMPLATE.read_text()))

    def test_every_section_is_required_in_order(self):
        for heading in ("## Why", "## What changed", "## Verification",
                        "## Problems found", "## Follow-ups", "## Reviewer notes"):
            body = GOOD_BODY.replace(heading, "## Other")
            self.assertTrue(any(heading in e for e in self.errors(body)), heading)
        swapped = GOOD_BODY.replace("## Why", "## TMP").replace(
            "## What changed", "## Why").replace("## TMP", "## What changed")
        self.assertTrue(any("order" in e for e in self.errors(swapped)))

    def test_verification_lines_are_fixed_prefixes(self):
        body = GOOD_BODY.replace("Gate: invariant 122/122 · fast 278/278 · 3f9c1e2",
                                 "Gate: green")
        self.assertTrue(any("Gate:" in e for e in self.errors(body)))
        body = GOOD_BODY.replace("Live: run 7b2e91aa ×1 on build 3f9c1e2 · $0.01",
                                 "Live: skipped")
        self.assertTrue(any("Live:" in e for e in self.errors(body)))
        body = GOOD_BODY.replace("Not verified: TAIFEX live", "Not verified:")
        self.assertTrue(any("Not verified:" in e for e in self.errors(body)))

    def test_live_not_run_needs_a_reason(self):
        ok = GOOD_BODY.replace("Live: run 7b2e91aa ×1 on build 3f9c1e2 · $0.01",
                               "Live: not run — no deployment serves this build")
        self.assertEqual([], self.errors(ok))
        bad = GOOD_BODY.replace("Live: run 7b2e91aa ×1 on build 3f9c1e2 · $0.01",
                                "Live: not run")
        self.assertTrue(any("Live:" in e for e in self.errors(bad)))

    def test_not_changed_line_is_required(self):
        body = GOOD_BODY.replace("Not changed: site-specific selectors.\n", "")
        self.assertTrue(any("Not changed:" in e for e in self.errors(body)))

    def test_none_is_accepted_for_optional_sections(self):
        body = GOOD_BODY.replace(
            "- Normal submits regressed to 30s waits → fast +12s → fixed: settle only when a\n"
            "  fetch was observed (case form-submit-no-pending-fetch).", "none")
        body = body.replace("- TAIFEX live probe on this build (case taifex-homepage-nav)", "none")
        self.assertEqual([], self.errors(body))

    def test_empty_section_fails(self):
        body = GOOD_BODY.replace(
            "- TAIFEX live probe on this build (case taifex-homepage-nav)\n", "")
        self.assertTrue(any("Follow-ups" in e for e in self.errors(body)))

    def test_follow_up_without_case_or_run_id_fails(self):
        body = GOOD_BODY.replace("- TAIFEX live probe on this build (case taifex-homepage-nav)",
                                 "- think about TAIFEX later")
        self.assertTrue(any("Follow-ups" in e for e in self.errors(body)))

    def test_reviewer_notes_need_start_and_reproduce(self):
        body = GOOD_BODY.replace("Reproduce: python3 -m evals.run --suite fast --case sec-homepage-async-submit", "")
        self.assertTrue(any("Reproduce:" in e for e in self.errors(body)))

    def test_blockquoted_task_headings_are_not_sections(self):
        # the task's own "## Description" / "## Acceptance Criteria" live inside a
        # blockquote so GitHub renders them and the six-section split ignores them
        self.assertEqual([], self.errors(GOOD_BODY))
        self.assertIn("> ## Description", GOOD_BODY)

    def test_unquoted_extra_heading_fails(self):
        # a raw paste of `backlog task view --plain` adds top-level sections; refuse it
        body = GOOD_BODY.replace("> ## Description", "## Description")
        self.assertTrue(any("Description" in e and "> " in e for e in self.errors(body)),
                        self.errors(body))

    def test_template_tells_the_author_to_blockquote_the_task(self):
        self.assertIn('prefixed with "> "', TEMPLATE.read_text())

    def test_html_comments_do_not_count_as_content(self):
        body = GOOD_BODY.replace(
            "- TAIFEX live probe on this build (case taifex-homepage-nav)",
            "<!-- one line each, with a case id -->")
        self.assertTrue(any("Follow-ups" in e for e in self.errors(body)))


class MainTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = load()

    def test_reads_github_event_and_exits_nonzero_on_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            event = Path(tmp) / "event.json"
            event.write_text(json.dumps({"pull_request": {"title": "Feat: bad", "body": GOOD_BODY}}))
            self.assertEqual(1, self.m.main(["--event", str(event)]))
            event.write_text(json.dumps({"pull_request": {"title": "feat: good", "body": GOOD_BODY}}))
            self.assertEqual(0, self.m.main(["--event", str(event)]))

    def test_title_only_mode_serves_the_commit_msg_hook(self):
        self.assertEqual(0, self.m.main(["--title-only", "--title", "fix(hooks): check commit subjects"]))
        self.assertEqual(1, self.m.main(["--title-only", "--title", "ready.py: id column width adapts"]))

    def test_reads_title_and_body_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            body = Path(tmp) / "body.md"
            body.write_text(GOOD_BODY)
            self.assertEqual(0, self.m.main(["--title", "fix: x", "--body-file", str(body)]))
            self.assertEqual(1, self.m.main(["--title", "fix: X", "--body-file", str(body)]))


if __name__ == "__main__":
    unittest.main()
