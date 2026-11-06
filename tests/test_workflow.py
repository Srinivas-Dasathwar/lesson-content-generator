"""
End-to-End Workflow Integration Tests.
Verifies the complete Generate -> Evaluate -> Feedback -> Regenerate Loop.
"""

import os
import tempfile
import unittest
from src.workflow import LessonGeneratorWorkflow
from src.providers.llm_provider import MockLLMProvider
from src.memory.institutional_memory import InstitutionalMemory


class TestWorkflow(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.mem_file = os.path.join(self.temp_dir, "test_memory.json")
        self.hist_file = os.path.join(self.temp_dir, "test_history.json")
        self.memory = InstitutionalMemory(memory_file=self.mem_file, history_file=self.hist_file)

    def test_standard_execution_passes(self):
        provider = MockLLMProvider(simulate_flaw_on_first_try=False)
        wf = LessonGeneratorWorkflow(llm_provider=provider, memory=self.memory, max_retries=2)
        state = wf.run(topic="RAG", flaw_injection="none")

        self.assertEqual(state.status, "PASSED")
        self.assertEqual(state.iteration, 0)
        self.assertEqual(len(state.rejection_history), 0)
        self.assertTrue(state.evaluation_result.overall_passed)

    def test_flaw_injection_triggers_rejection_and_successful_retry(self):
        # Flaw injected on round 1 (jargon_bomb), then auto-corrects on round 2
        provider = MockLLMProvider(simulate_flaw_on_first_try=True, flaw_type="jargon_bomb")
        wf = LessonGeneratorWorkflow(llm_provider=provider, memory=self.memory, max_retries=2)
        state = wf.run(topic="RAG", flaw_injection="jargon_bomb")

        self.assertEqual(state.status, "PASSED")
        self.assertEqual(state.iteration, 1)  # Retried on iteration 1
        self.assertEqual(len(state.rejection_history), 1)  # Exactly 1 rejection caught
        self.assertIn("NO_UNEXPLAINED_JARGON", state.rejection_history[0].failed_checkpoints)
        self.assertTrue(state.evaluation_result.overall_passed)

    def test_hallucination_flaw_triggers_rejection_and_recovery(self):
        provider = MockLLMProvider(simulate_flaw_on_first_try=True, flaw_type="hallucinated_facts")
        wf = LessonGeneratorWorkflow(llm_provider=provider, memory=self.memory, max_retries=2)
        state = wf.run(topic="RAG", flaw_injection="hallucinated_facts")

        self.assertEqual(state.status, "PASSED")
        self.assertEqual(state.iteration, 1)
        self.assertEqual(len(state.rejection_history), 1)
        self.assertIn("ACCURACY_AND_GROUNDING", state.rejection_history[0].failed_checkpoints)
        self.assertTrue(state.evaluation_result.overall_passed)


if __name__ == "__main__":
    unittest.main()
