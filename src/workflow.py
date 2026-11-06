"""
Stateful Agentic Workflow Orchestrator for Self-Evaluating Lesson Generation.
Coordinates Curriculum Planning -> Generation -> Evaluation -> Targeted Feedback -> Regeneration -> Memory Evolution.
"""

import logging
from typing import Optional, Dict, Any, Callable
from src.models import (
    WorkflowState,
    TargetAudience,
    RejectionRecord,
    LessonDraft,
    EvaluationResult
)
from src.providers.llm_provider import BaseLLMProvider, get_llm_provider
from src.agents.curriculum_planner import CurriculumPlannerAgent
from src.agents.lesson_generator import LessonGeneratorAgent
from src.evaluators.rubric_evaluator import RubricEvaluator
from src.memory.institutional_memory import InstitutionalMemory

logger = logging.getLogger(__name__)


class LessonGeneratorWorkflow:
    def __init__(
        self,
        llm_provider: Optional[BaseLLMProvider] = None,
        memory: Optional[InstitutionalMemory] = None,
        max_retries: int = 2
    ):
        self.memory = memory or InstitutionalMemory()
        self.max_retries = max_retries
        self.llm_provider = llm_provider or get_llm_provider()
        self.planner = CurriculumPlannerAgent(self.llm_provider)
        self.generator = LessonGeneratorAgent(self.llm_provider)
        self.evaluator = RubricEvaluator(self.llm_provider)

    def run(
        self,
        topic: str = "RAG (Retrieval-Augmented Generation)",
        flaw_injection: str = "none",
        audience: Optional[TargetAudience] = None,
        progress_callback: Optional[Callable[[str, Dict[str, Any]], None]] = None
    ) -> WorkflowState:
        """
        Executes the autonomous agentic loop.
        Guaranteed to terminate within max_retries.
        """
        audience = audience or TargetAudience()
        state = WorkflowState(
            topic=topic,
            audience=audience,
            max_retries=self.max_retries,
            flaw_injection=flaw_injection,
            status="INITIALIZED"
        )

        def notify(stage: str, data: Dict[str, Any]):
            logger.info(f"[{stage}] {data.get('message', '')}")
            state.execution_logs.append({"stage": stage, **data})
            if progress_callback:
                progress_callback(stage, data)

        notify("INIT", {"message": f"Starting autonomous lesson generation for '{topic}'", "flaw_injection": flaw_injection})

        # Step 1: Load Accumulated Institutional Memory
        memory_guidelines = self.memory.get_guidelines_for_prompt()
        state.accumulated_memory_rules = memory_guidelines
        notify("MEMORY_LOADED", {"message": f"Loaded {len(memory_guidelines)} institutional memory guardrails.", "rules": memory_guidelines})

        # Step 2: Curriculum Planning Node
        state.status = "PLANNING"
        notify("PLANNING", {"message": f"CurriculumPlannerAgent is structuring pedagogical milestones for {audience.persona}..."})
        curriculum_plan = self.planner.plan(topic, audience, memory_guidelines)
        notify("PLAN_CREATED", {"message": "Curriculum blueprint completed.", "plan": curriculum_plan})

        # Step 3: Generation & Evaluation Loop with Hard Pass/Fail
        previous_rejection: Optional[RejectionRecord] = None

        while state.iteration <= self.max_retries:
            is_retry = state.iteration > 0
            state.status = "REGENERATING" if is_retry else "GENERATING"

            notify(state.status, {
                "iteration": state.iteration,
                "message": f"{'Regenerating' if is_retry else 'Generating'} lesson draft (Round {state.iteration + 1} of {self.max_retries + 1})...",
                "is_retry": is_retry
            })

            # If flaw injection requested on first round
            if state.iteration == 0 and flaw_injection != "none":
                # Ensure the provider is configured to inject the flaw if using mock, or instruct generator
                notify("FLAW_INJECTION_ACTIVE", {"message": f"Simulating deliberate flaw: '{flaw_injection}' to test evaluator rigor."})

            draft: LessonDraft = self.generator.generate(
                topic=topic,
                audience=audience,
                curriculum_plan=curriculum_plan,
                memory_guidelines=memory_guidelines,
                previous_rejection=previous_rejection
            )
            state.current_draft = draft
            notify("DRAFT_GENERATED", {
                "iteration": state.iteration,
                "title": draft.title,
                "word_count": len(draft.full_markdown.split())
            })

            # Step 4: Multi-Stage Evaluator Node (Tier A Linter + Tier B Semantic Rubric)
            state.status = "EVALUATING"
            notify("EVALUATING", {"iteration": state.iteration, "message": "RubricEvaluator is auditing draft across 6 hard pass/fail checkpoints..."})

            eval_result: EvaluationResult = self.evaluator.evaluate(draft, audience)
            state.evaluation_result = eval_result

            failed_cps = [cp.checkpoint_id for cp in eval_result.checkpoints if not cp.passed]
            passed_cps = [cp.checkpoint_id for cp in eval_result.checkpoints if cp.passed]

            notify("EVALUATION_COMPLETE", {
                "iteration": state.iteration,
                "overall_passed": eval_result.overall_passed,
                "passed_count": len(passed_cps),
                "failed_count": len(failed_cps),
                "summary": eval_result.summary
            })

            # Branch Decision
            if eval_result.overall_passed:
                state.status = "PASSED"
                notify("PASSED", {
                    "iteration": state.iteration,
                    "message": "Lesson APPROVED. All 6 rubric checkpoints cleared. Lesson is ready to ship!"
                })
                break
            else:
                # Formulation of Rejection Record
                root_causes = "\n".join([f"- [{cp.checkpoint_id}] {cp.critique}" for cp in eval_result.checkpoints if not cp.passed])
                remedies = "\n".join([f"- [{cp.checkpoint_id}] {cp.actionable_remedy or 'Revise as instructed'}" for cp in eval_result.checkpoints if not cp.passed])

                rejection = RejectionRecord(
                    iteration=state.iteration,
                    failed_checkpoints=failed_cps,
                    root_cause_analysis=root_causes,
                    feedback_injected_to_prompt=f"Fix the following rubric failures:\n{root_causes}\n\nRequired Remedies:\n{remedies}",
                    remedy_applied=remedies
                )
                state.rejection_history.append(rejection)

                # Self-Evolution Node: Learn from rejection into institutional memory
                self.memory.learn_from_rejection(rejection)
                notify("MEMORY_EVOLVED", {
                    "iteration": state.iteration,
                    "message": "Institutional memory updated with new distilled negative constraints from rejection."
                })

                if state.iteration >= self.max_retries:
                    state.status = "MAX_RETRIES_EXCEEDED"
                    notify("MAX_RETRIES_REACHED", {
                        "iteration": state.iteration,
                        "message": f"Loop terminated: Reached maximum retries ({self.max_retries}). Shipping best effort with rejection audit."
                    })
                    break

                # Prepare for retry
                previous_rejection = rejection
                state.iteration += 1

        # Final record keeping
        self.memory.record_run({
            "topic": topic,
            "final_status": state.status,
            "total_iterations": state.iteration + 1,
            "rejections_count": len(state.rejection_history),
            "rejection_history": [r.model_dump() for r in state.rejection_history]
        })

        return state
