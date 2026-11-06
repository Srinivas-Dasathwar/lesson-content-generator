"""
Tier A Evaluator: Fast Deterministic Heuristic Linter.
Catches structural deficiencies, excessive sentence complexity, and unexplained high-dimensional
technical jargon before passing content to the LLM semantic judge.
"""

import re
from typing import List, Dict, Any, Tuple
from src.models import LessonDraft

# Unexplained graduate-level AI/ML jargon that should never appear without explicit simplification
PROHIBITED_JARGON_PATTERNS = [
    r"\bmanifold degradation\b",
    r"\bhnsw\b",
    r"\bvector space\b",
    r"\beuclidean\b",
    r"\bcosine similarity\b",
    r"\bbi-encoder\b",
    r"\bcross-encoder\b",
    r"\bbackpropagation\b",
    r"\bgradient descent\b",
    r"\blatent space\b",
    r"\bautoregressive probabilistic\b",
    r"\bnon-parametric external corpus\b",
    r"\btokenization\b",
    r"\b1536-dimensional\b",
    r"\bdot-product computation\b"
]

MANDATORY_SECTIONS = [
    ("hook", "Hook / Curiosity Opening"),
    ("everyday_analogy", "Everyday Relatable Analogy"),
    ("problem_statement", "The Problem (Why AI needs this)"),
    ("how_it_works", "Step-by-step How it works"),
    ("concept_check_quiz", "Concept Check Practice Quiz"),
    ("summary_and_next_steps", "Summary & Next Steps")
]


class DeterministicLinter:
    def __init__(self, max_sentence_words: int = 32, max_avg_sentence_words: int = 22):
        self.max_sentence_words = max_sentence_words
        self.max_avg_sentence_words = max_avg_sentence_words

    def lint(self, draft: LessonDraft) -> Tuple[bool, List[str], List[Dict[str, Any]]]:
        """
        Runs deterministic heuristic checks.
        Returns:
            passed (bool): True if zero hard violations.
            violations (List[str]): High-level violation summaries.
            details (List[Dict[str, Any]]): Granular diagnostic reports.
        """
        violations = []
        details = []

        full_text = f"{draft.hook}\n{draft.everyday_analogy}\n{draft.problem_statement}\n{draft.how_it_works}\n{draft.concept_check_quiz}\n{draft.summary_and_next_steps}"

        # 1. Check for Forbidden High-Dimensional Jargon
        for pattern in PROHIBITED_JARGON_PATTERNS:
            matches = re.findall(pattern, full_text, flags=re.IGNORECASE)
            if matches:
                matched_term = matches[0]
                # Allow if explicitly paired with an everyday explanation like "which means" or "think of it as"
                context_match = re.search(rf"{pattern}.{{0,50}}(?:means|think of|like|simple)", full_text, flags=re.IGNORECASE)
                if not context_match:
                    violations.append(f"Forbidden graduate-level technical jargon detected without simplification: '{matched_term}'")
                    details.append({
                        "check": "FORBIDDEN_JARGON",
                        "status": "FAIL",
                        "term": matched_term,
                        "remedy": f"Remove '{matched_term}' or explain it with an everyday Indian analogy (e.g. library index card)."
                    })

        # 2. Check Structural Completeness
        for attr, section_name in MANDATORY_SECTIONS:
            content = getattr(draft, attr, "").strip()
            if len(content) < 30:
                violations.append(f"Mandatory section '{section_name}' is missing or too brief ({len(content)} chars).")
                details.append({
                    "check": "STRUCTURAL_COMPLETENESS",
                    "status": "FAIL",
                    "section": section_name,
                    "remedy": f"Flesh out '{section_name}' with at least 2 full beginner-friendly paragraphs."
                })

        # 3. Check Sentence Length & Complexity (Accessibility for 12th Pass Non-English Medium)
        sentences = [s.strip() for s in re.split(r'[.!?]+', full_text) if s.strip()]
        if sentences:
            sentence_word_counts = [len(s.split()) for s in sentences]
            avg_words = sum(sentence_word_counts) / len(sentences)
            run_on_sentences = [s for s in sentences if len(s.split()) > self.max_sentence_words]

            if avg_words > self.max_avg_sentence_words:
                violations.append(f"Average sentence length is too high ({avg_words:.1f} words/sentence, max allowed is {self.max_avg_sentence_words}). Break sentences into shorter thoughts.")
                details.append({
                    "check": "READABILITY_SENTENCE_LENGTH",
                    "status": "FAIL",
                    "avg_words": avg_words,
                    "remedy": "Break complex sentences with conjunctions ('and', 'which', 'furthermore') into crisp 10-15 word sentences."
                })

            if len(run_on_sentences) > 2:
                violations.append(f"Found {len(run_on_sentences)} run-on sentences with over {self.max_sentence_words} words each.")
                details.append({
                    "check": "RUN_ON_SENTENCES",
                    "status": "FAIL",
                    "sample": run_on_sentences[0][:100] + "...",
                    "remedy": "Split long sentences into 2 or 3 shorter, punchier statements."
                })

        passed = len(violations) == 0
        return passed, violations, details
