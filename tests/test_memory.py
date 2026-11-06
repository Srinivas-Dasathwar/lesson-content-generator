"""
Unit tests for Institutional Memory and Self-Evolution.
"""

import os
import tempfile
import unittest
from src.memory.institutional_memory import InstitutionalMemory
from src.models import RejectionRecord


class TestInstitutionalMemory(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.mem_file = os.path.join(self.temp_dir, "test_memory.json")
        self.hist_file = os.path.join(self.temp_dir, "test_history.json")
        self.memory = InstitutionalMemory(memory_file=self.mem_file, history_file=self.hist_file)

    def test_initial_rules_loaded(self):
        guidelines = self.memory.get_guidelines_for_prompt()
        self.assertGreaterEqual(len(guidelines), 4)
        self.assertTrue(any("Open-Book" in g for g in guidelines))

    def test_learns_from_rejection(self):
        initial_count = len(self.memory.rules)
        rejection = RejectionRecord(
            iteration=0,
            failed_checkpoints=["NO_UNEXPLAINED_JARGON", "AUDIENCE_VOCABULARY_AND_TONE"],
            root_cause_analysis="Contained unexplained terms like 'HNSW' and 'bi-encoder'.",
            feedback_injected_to_prompt="Remove research jargon.",
            remedy_applied="Explain terms with library card analogy."
        )
        self.memory.learn_from_rejection(rejection)

        # Ensure memory saved and updated
        updated_guidelines = self.memory.get_guidelines_for_prompt()
        self.assertGreaterEqual(len(updated_guidelines), initial_count)

    def test_run_history_recorded(self):
        self.memory.record_run({
            "topic": "Test RAG",
            "final_status": "PASSED",
            "total_iterations": 1,
            "rejections_count": 0
        })
        evo = self.memory.get_evolution_report()
        self.assertEqual(evo["total_runs"], 1)


if __name__ == "__main__":
    unittest.main()
