"""Keep Groundwork's self-tests out of the project template scaffold."""

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class RepositoryBoundaryTests(unittest.TestCase):
    def test_template_evals_contain_no_groundwork_cases_or_history(self):
        allowed = {
            "evals/run.py",
            "evals/golden/.gitkeep",
            "evals/adversarial/.gitkeep",
            "evals/report/.gitkeep",
        }
        files = self._source_files(ROOT / "evals")

        self.assertEqual(allowed, {str(path.relative_to(ROOT)) for path in files})

    def test_template_src_is_empty(self):
        files = self._source_files(ROOT / "src")

        self.assertEqual({"src/.gitkeep"}, {str(path.relative_to(ROOT)) for path in files})

    def test_template_specs_contain_no_groundwork_contracts(self):
        files = self._source_files(ROOT / "specs")

        self.assertEqual(
            {"specs/000-invariants.md"},
            {str(path.relative_to(ROOT)) for path in files},
        )

    @staticmethod
    def _source_files(root):
        return sorted(
            path for path in root.rglob("*")
            if path.is_file() and "__pycache__" not in path.parts
        )


if __name__ == "__main__":
    unittest.main()
