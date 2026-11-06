"""
Data models and state definitions for the Self-Evaluating Lesson Content Generator.
"""

from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime


class TargetAudience(BaseModel):
    persona: str = "12th-grade graduate from India"
    language_proficiency: str = "Limited English vocabulary, non-English-medium background"
    motivation: str = "Wants to kickstart an AI/software career from scratch"
    learning_style: str = "Intuitive, analogy-driven, needs real-world everyday examples"
    cultural_context: str = "Indian everyday references (e.g., exams, library, local stores, railway ticketing)"


class CheckpointEvaluation(BaseModel):
    checkpoint_id: str
    dimension_name: str
    passed: bool
    score_desc: str = Field(description="Strict PASS or FAIL with justification")
    critique: str = Field(description="Detailed explanation of why it passed or failed")
    snippet_citation: Optional[str] = Field(default=None, description="Exact text excerpt violating or satisfying the rubric")
    actionable_remedy: Optional[str] = Field(default=None, description="Specific instructions on how to fix this in regeneration")


class EvaluationResult(BaseModel):
    overall_passed: bool
    checkpoints: List[CheckpointEvaluation]
    summary: str
    evaluated_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class RejectionRecord(BaseModel):
    iteration: int
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    failed_checkpoints: List[str]
    root_cause_analysis: str
    feedback_injected_to_prompt: str
    remedy_applied: str
    rejected_draft_title: Optional[str] = None
    rejected_draft_snippet: Optional[str] = None


class LessonDraft(BaseModel):
    topic: str
    title: str
    hook: str
    everyday_analogy: str
    problem_statement: str
    how_it_works: str
    mental_model_diagram: str
    concept_check_quiz: str
    summary_and_next_steps: str
    full_markdown: str


class MemoryRule(BaseModel):
    rule_id: str
    category: Literal["VOCABULARY", "ANALOGY", "JARGON", "STRUCTURE", "GROUNDING"]
    directive: str
    source_failure: str
    occurrence_count: int = 1
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class WorkflowState(BaseModel):
    topic: str
    audience: TargetAudience = Field(default_factory=TargetAudience)
    iteration: int = 0
    max_retries: int = 2
    status: Literal["INITIALIZED", "PLANNING", "GENERATING", "EVALUATING", "REGENERATING", "PASSED", "MAX_RETRIES_EXCEEDED"] = "INITIALIZED"
    current_draft: Optional[LessonDraft] = None
    evaluation_result: Optional[EvaluationResult] = None
    rejection_history: List[RejectionRecord] = Field(default_factory=list)
    accumulated_memory_rules: List[str] = Field(default_factory=list)
    flaw_injection: Optional[Literal["none", "jargon_bomb", "hallucinated_facts", "missing_analogy"]] = "none"
    execution_logs: List[Dict[str, Any]] = Field(default_factory=list)
