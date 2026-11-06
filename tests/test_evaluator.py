"""
Unit tests for the Deterministic Linter and Rubric Evaluator.
"""

import unittest
from src.models import LessonDraft, TargetAudience
from src.evaluators.deterministic_linter import DeterministicLinter
from src.evaluators.rubric_evaluator import RubricEvaluator
from src.providers.llm_provider import MockLLMProvider


class TestEvaluators(unittest.TestCase):
    def setUp(self):
        self.linter = DeterministicLinter()
        self.audience = TargetAudience()

    def test_linter_catches_jargon_bomb(self):
        flawed_draft = LessonDraft(
            topic="RAG",
            title="Complex RAG",
            hook="Let us study manifold degradation.",
            everyday_analogy="Imagine an HNSW graph in 1536-dimensional space.",
            problem_statement="Requires backpropagation and gradient descent.",
            how_it_works="Computes dot-product computation with cross-encoder.",
            mental_model_diagram="Diagram",
            concept_check_quiz="Quiz",
            summary_and_next_steps="Summary",
            full_markdown="Content"
        )
        passed, violations, details = self.linter.lint(flawed_draft)
        self.assertFalse(passed)
        self.assertTrue(any("jargon detected" in v.lower() for v in violations))

    def test_linter_passes_clean_content(self):
        clean_draft = LessonDraft(
            topic="RAG",
            title="Simple RAG for Beginners",
            hook="Why does AI sometimes guess wrong answers? Let us find out with an open-book exam trick.",
            everyday_analogy="Think of an Open-Book Exam. Instead of memorizing everything, you check your textbook.",
            problem_statement="AI models make up facts or forget recent news. Training them costs too much money.",
            how_it_works="Step 1: Search the notes. Step 2: Attach the facts to the question. Step 3: Write the answer.",
            mental_model_diagram="Question -> Search Book -> Attach Fact -> AI Writes Answer.",
            concept_check_quiz="Question: Does RAG change AI weights? Answer: No, it only looks up reference notes.",
            summary_and_next_steps="Remember: RAG is search plus generation. Next, we learn search index cards.",
            full_markdown="Clean Content"
        )
        passed, violations, details = self.linter.lint(clean_draft)
        self.assertTrue(passed)
        self.assertEqual(len(violations), 0)

    def test_rubric_evaluator_catches_flaw_and_recovers(self):
        # Test that Mock provider with jargon_bomb fails on evaluation
        flawed_provider = MockLLMProvider(simulate_flaw_on_first_try=True, flaw_type="jargon_bomb")
        evaluator = RubricEvaluator(flawed_provider)

        flawed_draft = LessonDraft(
            topic="RAG",
            title="High Dimensional RAG",
            hook="Modern deep generative transformers suffer from manifold degradation.",
            everyday_analogy="Euclidean vector space with cosine similarity.",
            problem_statement="Autoregressive probabilistic token sampling.",
            how_it_works="1536-dimensional float32 dense tensors indexed via HNSW graphs.",
            mental_model_diagram="Corpus -> Bi-Encoder -> Vectors",
            concept_check_quiz="Quiz on O(N*d) complexity",
            summary_and_next_steps="Next: Contrastive loss",
            full_markdown="Flawed text"
        )

        res = evaluator.evaluate(flawed_draft, self.audience)
        self.assertFalse(res.overall_passed)
        failed_ids = [cp.checkpoint_id for cp in res.checkpoints if not cp.passed]
        self.assertIn("AUDIENCE_VOCABULARY_AND_TONE", failed_ids)
        self.assertIn("NO_UNEXPLAINED_JARGON", failed_ids)


if __name__ == "__main__":
    unittest.main()
