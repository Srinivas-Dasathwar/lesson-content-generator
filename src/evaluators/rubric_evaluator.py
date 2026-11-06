"""
Tier B Evaluator: Strict LLM-as-a-Judge with Hard Pass/Fail Rubric Checkpoints.
Enforces the 6 core pedagogical and technical dimensions with zero partial credit.
Combines deterministic linter results with semantic critique.
"""

import json
import logging
from typing import Dict, Any, List
from src.models import (
    LessonDraft,
    EvaluationResult,
    CheckpointEvaluation,
    TargetAudience
)
from src.evaluators.deterministic_linter import DeterministicLinter
from src.providers.llm_provider import BaseLLMProvider

logger = logging.getLogger(__name__)

RUBRIC_SYSTEM_PROMPT = """You are the Lead Curriculum Quality Auditor for an advanced AI learning platform.
Your role is to rigorously judge educational lessons designed for:
TARGET LEARNER: A 12th-grade graduate from India, from a non-English-medium school, with limited English vocabulary, who wants to kickstart a tech/AI career.

You operate a strict HARD PASS/FAIL evaluation rubric with NO PARTIAL CREDIT.
A lesson is either 100% ready to ship to a beginner learner, or it must be rejected for targeted regeneration.

You must evaluate the lesson across exactly SIX Hard Pass/Fail Checkpoints:

1. ACCURACY_AND_GROUNDING:
   - PASS: Core mechanics of RAG are factually truthful. Retrieval is clearly separated from Generation. Explicitly DOES NOT claim RAG fine-tunes or retrains model weights.
   - FAIL: Any factual inaccuracy, claiming that RAG retrains model weights on every prompt, or confusing RAG with model fine-tuning.

2. AUDIENCE_VOCABULARY_AND_TONE:
   - PASS: Simple, clear, conversational English suitable for 12th-grade non-English medium students. Short sentences, warm, encouraging tone.
   - FAIL: Academic, high-brow, GRE/CAT-level vocabulary (e.g. 'manifold', 'stochastic', 'non-parametric', 'dichotomy') or dry textbook tone.

3. RELATABLE_ANALOGY:
   - PASS: Contains a vivid, relatable everyday analogy (e.g. Open-Book Exam vs Closed-Book Exam, or library reference) that maps 1:1 to RAG concepts.
   - FAIL: Missing analogy, or analogy is abstract, mathematical, or inaccessible to everyday Indian life.

4. NO_UNEXPLAINED_JARGON:
   - PASS: Every technical term (Retrieval, Augmentation, Hallucination, Prompt, Context) is explained in simple everyday words before or alongside usage.
   - FAIL: Drops AI buzzwords (like 'HNSW', 'Vector space', 'Cosine distance', 'Latent embeddings') without grounding metaphors.

5. KEY_PILLARS_COVERAGE:
   - PASS: Explicitly and clearly covers all 3 pillars: WHAT is RAG, WHY it matters (hallucination, outdated data, privacy), and HOW it works (Retrieve, Augment, Generate).
   - FAIL: Skips or rushes past any of What, Why, or How.

6. COHERENT_TEACHING_FLOW:
   - PASS: Seamless pedagogical progression: Hook -> Analogy -> The Core Problem -> How RAG solves it -> Step-by-Step Flow -> Interactive Concept Check Quiz (with immediate answer and explanation) -> Key Takeaway Summary.
   - FAIL: Disjointed jumps, missing quiz, or quiz asking PhD/computational complexity questions.

RULES:
- If ANY single checkpoint is FAIL, 'overall_passed' MUST be false.
- For every checkpoint, provide the exact quote ('snippet_citation') and actionable fix instructions ('actionable_remedy') if failed.
- Return ONLY valid JSON matching the specified schema.
"""

class RubricEvaluator:
    def __init__(self, llm_provider: BaseLLMProvider):
        self.llm_provider = llm_provider
        self.linter = DeterministicLinter()

    def evaluate(self, draft: LessonDraft, audience: TargetAudience) -> EvaluationResult:
        # Step 1: Run Tier A deterministic linter
        linter_passed, linter_violations, linter_details = self.linter.lint(draft)

        # Step 2: Prepare prompt for Tier B LLM semantic judge
        prompt = f"""EVALUATION_TASK:
Please evaluate the following lesson draft against the strict 6-checkpoint rubric.

TOPIC: {draft.topic}
TARGET AUDIENCE: {audience.persona} | {audience.language_proficiency}

DRAFT TO EVALUATE:
----------------------------------------
TITLE: {draft.title}

HOOK:
{draft.hook}

EVERYDAY ANALOGY:
{draft.everyday_analogy}

THE PROBLEM IT SOLVES:
{draft.problem_statement}

HOW IT WORKS (STEP BY STEP):
{draft.how_it_works}

MENTAL MODEL DIAGRAM:
{draft.mental_model_diagram}

CONCEPT CHECK QUIZ:
{draft.concept_check_quiz}

SUMMARY & NEXT STEPS:
{draft.summary_and_next_steps}
----------------------------------------

DETERMINISTIC LINTER FINDINGS:
{json.dumps(linter_violations, indent=2) if linter_violations else "Zero deterministic rule violations detected."}

Provide evaluation output in this exact JSON structure:
{{
  "overall_passed": true/false,
  "summary": "High-level summary of verdict",
  "checkpoints": [
    {{
      "checkpoint_id": "ACCURACY_AND_GROUNDING",
      "dimension_name": "Accurate & Grounded",
      "passed": true/false,
      "score_desc": "PASS or FAIL",
      "critique": "Reasoning...",
      "snippet_citation": "Quote from text or null",
      "actionable_remedy": "How to fix or null"
    }},
    {{
      "checkpoint_id": "AUDIENCE_VOCABULARY_AND_TONE",
      "dimension_name": "Beginner-Friendly Language (12th Grade India)",
      "passed": true/false,
      "score_desc": "PASS or FAIL",
      "critique": "Reasoning...",
      "snippet_citation": "Quote from text or null",
      "actionable_remedy": "How to fix or null"
    }},
    {{
      "checkpoint_id": "RELATABLE_ANALOGY",
      "dimension_name": "Teaches by Relatable Example/Analogy",
      "passed": true/false,
      "score_desc": "PASS or FAIL",
      "critique": "Reasoning...",
      "snippet_citation": "Quote from text or null",
      "actionable_remedy": "How to fix or null"
    }},
    {{
      "checkpoint_id": "NO_UNEXPLAINED_JARGON",
      "dimension_name": "Clear, No Unexplained Jargon",
      "passed": true/false,
      "score_desc": "PASS or FAIL",
      "critique": "Reasoning...",
      "snippet_citation": "Quote from text or null",
      "actionable_remedy": "How to fix or null"
    }},
    {{
      "checkpoint_id": "CORE_PILLARS_COVERAGE",
      "dimension_name": "Covers Key Points (What, Why, How)",
      "passed": true/false,
      "score_desc": "PASS or FAIL",
      "critique": "Reasoning...",
      "snippet_citation": "Quote from text or null",
      "actionable_remedy": "How to fix or null"
    }},
    {{
      "checkpoint_id": "COHERENT_TEACHING_FLOW",
      "dimension_name": "Coherent Pedagogical Flow & Concept Check",
      "passed": true/false,
      "score_desc": "PASS or FAIL",
      "critique": "Reasoning...",
      "snippet_citation": "Quote from text or null",
      "actionable_remedy": "How to fix or null"
    }}
  ]
}}
"""

        try:
            raw_eval = self.llm_provider.generate_json(prompt, system_prompt=RUBRIC_SYSTEM_PROMPT)
            checkpoints = [CheckpointEvaluation(**cp) for cp in raw_eval.get("checkpoints", [])]

            # If deterministic linter failed, force fail corresponding checkpoints
            if not linter_passed:
                for violation in linter_violations:
                    if "jargon detected" in violation.lower():
                        cp_jargon = next((c for c in checkpoints if c.checkpoint_id == "NO_UNEXPLAINED_JARGON"), None)
                        if cp_jargon:
                            cp_jargon.passed = False
                            cp_jargon.score_desc = "FAIL"
                            cp_jargon.critique = f"{cp_jargon.critique} | Linter flagged: {violation}"
                    if "sentence length" in violation.lower():
                        cp_vocab = next((c for c in checkpoints if c.checkpoint_id == "AUDIENCE_VOCABULARY_AND_TONE"), None)
                        if cp_vocab:
                            cp_vocab.passed = False
                            cp_vocab.score_desc = "FAIL"
                            cp_vocab.critique = f"{cp_vocab.critique} | Linter flagged: {violation}"

            # Strict rule: overall_passed is True IF AND ONLY IF every single checkpoint is True
            all_passed = all(cp.passed for cp in checkpoints)

            summary = raw_eval.get("summary", "")
            if not all_passed and "APPROVED" in summary:
                summary = "REJECTED: One or more rubric checkpoints failed."

            return EvaluationResult(
                overall_passed=all_passed,
                checkpoints=checkpoints,
                summary=summary
            )

        except Exception as e:
            logger.error(f"Error during semantic evaluation: {e}. Falling back to deterministic fail.")
            # Fallback evaluation on error
            return EvaluationResult(
                overall_passed=False,
                summary=f"Evaluation execution error: {str(e)}",
                checkpoints=[
                    CheckpointEvaluation(
                        checkpoint_id="EXECUTION_ERROR",
                        dimension_name="Evaluation Pipeline Integrity",
                        passed=False,
                        score_desc="FAIL",
                        critique=f"Evaluation failed to complete: {str(e)}",
                        actionable_remedy="Retry generation with standard payload."
                    )
                ]
            )
