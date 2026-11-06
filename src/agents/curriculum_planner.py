"""
Curriculum Planner Agent.
Structures the pedagogical progression for the lesson, ensuring it meets the cognitive
needs of a 12th-grade Indian student starting from zero.
"""

import json
import logging
from typing import Dict, Any, List
from src.models import TargetAudience
from src.providers.llm_provider import BaseLLMProvider

logger = logging.getLogger(__name__)

PLANNER_SYSTEM_PROMPT = """You are a Master Curriculum Architect for NxtWave.
Your goal is to outline a high-impact, beginner-friendly lesson plan for a student who:
- Just finished 12th grade in India.
- Comes from a non-English-medium school.
- Has limited English vocabulary and ZERO prior knowledge of Artificial Intelligence.
- Is eager to learn and needs intuitive, physical analogies rather than abstract math.

Design a 6-part pedagogical structure:
1. The Hook (Relatable real-world curiosity)
2. Everyday Analogy (e.g. Open-Book vs Closed-Book exam, library register)
3. The Core Problem with Plain AI (Why RAG is needed: outdated facts, hallucinations, privacy)
4. Step-by-step How it Works (Retrieve -> Augment -> Generate)
5. Mental Model / Flow
6. Concept Check Scenario Quiz (Real-world Indian student context)

Return ONLY valid JSON.
"""

class CurriculumPlannerAgent:
    def __init__(self, llm_provider: BaseLLMProvider):
        self.llm_provider = llm_provider

    def plan(self, topic: str, audience: TargetAudience, memory_guidelines: List[str]) -> Dict[str, Any]:
        prompt = f"""CURRICULUM_PLANNING_TASK:
Create a detailed curriculum plan for the topic: '{topic}'

TARGET AUDIENCE:
- Persona: {audience.persona}
- English Level: {audience.language_proficiency}
- Cultural Reference: {audience.cultural_context}

INSTITUTIONAL MEMORY GUIDELINES (Must adhere):
{json.dumps(memory_guidelines, indent=2)}

Return JSON with:
{{
  "topic": "{topic}",
  "hook": "...",
  "analogy": "...",
  "the_problem": "...",
  "rag_definition": "...",
  "step_by_step": ["Step 1...", "Step 2...", "Step 3..."],
  "quiz_question": "...",
  "summary": "..."
}}
"""
        return self.llm_provider.generate_json(prompt, system_prompt=PLANNER_SYSTEM_PROMPT)
