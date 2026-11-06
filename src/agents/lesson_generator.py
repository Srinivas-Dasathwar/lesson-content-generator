"""
Lesson Generator Agent.
Synthesizes the complete beginner-friendly lesson draft based on curriculum plan,
target persona adaptation, accumulated institutional memory, and rejection feedback on retry.
"""

import json
import logging
from typing import Dict, Any, List, Optional
from src.models import LessonDraft, TargetAudience, RejectionRecord
from src.providers.llm_provider import BaseLLMProvider

logger = logging.getLogger(__name__)

GENERATOR_SYSTEM_PROMPT = """You are an Elite Technical Content Educator.
Your mission is to write an engaging, crystal-clear, standalone beginner lesson for:
TARGET LEARNER:
- 12th-grade graduate from India.
- Non-English-medium educational background.
- Limited English vocabulary (keep sentences under 20 words, avoid fancy GRE/CAT words).
- Zero prior AI knowledge.
- Ambitious and wants to kickstart a high-growth tech career.

PEDAGOGICAL TEACHING RULES:
1. Explain WHAT it is, WHY it matters, and HOW it works from absolute zero.
2. Teach through relatable Indian everyday life analogies (e.g. Open-Book Exam vs Closed-Book Exam, or library reference desk).
3. Zero unexplained jargon: NEVER introduce terms like 'Embeddings' or 'Vector Database' without first explaining them as 'Search Numbers' or 'Library Catalog Cards'.
4. Grounded & Accurate: Clarify that RAG DOES NOT retrain the AI model or change its weights; it simply hands reference notes into the prompt.
5. Provide a clear ASCII / Visual Flow Diagram of the 3 steps: Retrieval -> Augmentation -> Generation.
6. Include a 1-minute Concept Check Quiz with an everyday scenario question, clear options, correct answer, and explanation.
7. End with an encouraging summary and next steps.

Output MUST be valid JSON with keys:
- topic, title, hook, everyday_analogy, problem_statement, how_it_works, mental_model_diagram, concept_check_quiz, summary_and_next_steps, full_markdown.
"""

class LessonGeneratorAgent:
    def __init__(self, llm_provider: BaseLLMProvider):
        self.llm_provider = llm_provider

    def generate(
        self,
        topic: str,
        audience: TargetAudience,
        curriculum_plan: Dict[str, Any],
        memory_guidelines: List[str],
        previous_rejection: Optional[RejectionRecord] = None
    ) -> LessonDraft:
        
        feedback_section = ""
        if previous_rejection:
            feedback_section = f"""
========================================================================
CRITICAL: PREVIOUS REJECTION FEEDBACK (ROUND {previous_rejection.iteration})
Your previous draft was REJECTED by the Quality Rubric Evaluator.
You MUST fix the following exact issues in this regeneration:

FAILED CHECKPOINTS:
{json.dumps(previous_rejection.failed_checkpoints, indent=2)}

ROOT CAUSE ANALYSIS:
{previous_rejection.root_cause_analysis}

SPECIFIC REMEDIAL ACTION REQUIRED:
{previous_rejection.remedy_applied}
========================================================================
"""

        prompt = f"""LESSON_GENERATION_TASK:
Generate the standalone beginner lesson on: '{topic}'

TARGET AUDIENCE:
- Persona: {audience.persona}
- English Background: {audience.language_proficiency}
- Learning Style: {audience.learning_style}

CURRICULUM BLUEPRINT:
{json.dumps(curriculum_plan, indent=2)}

ACCUMULATED INSTITUTIONAL MEMORY (Learned from past runs):
{json.dumps(memory_guidelines, indent=2)}
{feedback_section}

Return the completed lesson strictly as a JSON object with these fields:
{{
  "topic": "{topic}",
  "title": "Inspiring, crystal-clear title",
  "hook": "Relatable 2-3 sentence hook",
  "everyday_analogy": "Deep, vivid Open-Book Exam vs Closed-Book Exam analogy",
  "problem_statement": "3 simple reasons why plain AI needs RAG (Hallucinations, Outdated facts, Privacy)",
  "how_it_works": "The 3 simple steps: R (Retrieve), A (Augment), G (Generate)",
  "mental_model_diagram": "Clear text/ASCII diagram of the 3-step flow",
  "concept_check_quiz": "Real-world Indian student scenario quiz with options, correct answer, and explanation",
  "summary_and_next_steps": "3 key takeaways to remember + exciting preview of next lesson"
}}
"""
        raw_draft = self.llm_provider.generate_json(prompt, system_prompt=GENERATOR_SYSTEM_PROMPT)

        # Assemble full markdown document
        title = raw_draft.get("title", f"Introduction to {topic}")
        hook = raw_draft.get("hook", "")
        everyday_analogy = raw_draft.get("everyday_analogy", "")
        problem_statement = raw_draft.get("problem_statement", "")
        how_it_works = raw_draft.get("how_it_works", "")
        mental_model_diagram = raw_draft.get("mental_model_diagram", "")
        concept_check_quiz = raw_draft.get("concept_check_quiz", "")
        summary_and_next_steps = raw_draft.get("summary_and_next_steps", "")

        full_markdown = f"""# {title}
*Topic: {topic} | Level: Absolute Beginner (Zero Prior Knowledge Required)*

---

## 🎯 1. The Hook: Why Does ChatGPT Sometimes Make Things Up?
{hook}

---

## 💡 2. The Big Analogy: Open-Book Exam vs Closed-Book Exam
{everyday_analogy}

---

## ⚠️ 3. The Real Problem with Plain AI
{problem_statement}

---

## ⚙️ 4. How RAG Works: Step-by-Step
{how_it_works}

### 🗺️ The 3-Step Mental Flow Map
{mental_model_diagram}

---

## 🧠 5. 1-Minute Concept Check (Test Yourself!)
{concept_check_quiz}

---

## 🚀 6. Summary & What to Learn Next
{summary_and_next_steps}
"""

        return LessonDraft(
            topic=topic,
            title=title,
            hook=hook,
            everyday_analogy=everyday_analogy,
            problem_statement=problem_statement,
            how_it_works=how_it_works,
            mental_model_diagram=mental_model_diagram,
            concept_check_quiz=concept_check_quiz,
            summary_and_next_steps=summary_and_next_steps,
            full_markdown=full_markdown
        )
