"""
Persistent Institutional Memory and Self-Evolution System.
Persists across runs in data/institutional_memory.json and learns from feedback/rejections
to continually sharpen generation prompts and evaluator rules.
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from src.models import MemoryRule, RejectionRecord

logger = logging.getLogger(__name__)

DEFAULT_MEMORY_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "data",
    "institutional_memory.json"
)

DEFAULT_HISTORY_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "data",
    "run_history.json"
)


class InstitutionalMemory:
    def __init__(self, memory_file: str = DEFAULT_MEMORY_FILE, history_file: str = DEFAULT_HISTORY_FILE):
        self.memory_file = memory_file
        self.history_file = history_file
        self.rules: List[MemoryRule] = []
        self.run_history: List[Dict[str, Any]] = []
        self._load()

    def _load(self):
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.memory_file), exist_ok=True)

        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.rules = [MemoryRule(**r) for r in data.get("rules", [])]
            except Exception as e:
                logger.warning(f"Failed to read memory file ({e}). Starting fresh.")
                self.rules = []
        else:
            self._seed_default_rules()

        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    self.run_history = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to read history file ({e}).")
                self.run_history = []

    def _seed_default_rules(self):
        """Seed initial distilled guidelines learned from early content engineering experiments."""
        self.rules = [
            MemoryRule(
                rule_id="RULE-VOCAB-001",
                category="VOCABULARY",
                directive="Keep English vocabulary accessible for 12th-grade Indian graduates from non-English medium backgrounds. Prefer 'simple, everyday words' over academic jargon.",
                source_failure="Initial pilots used words like 'parametric', 'dichotomy', and 'stochastic' which disengaged beginners.",
                occurrence_count=3
            ),
            MemoryRule(
                rule_id="RULE-ANALOGY-001",
                category="ANALOGY",
                directive="Anchor RAG in the 'Open-Book Exam vs Closed-Book Exam' analogy. It instantly clicks with Indian students who understand exam pressure.",
                source_failure="Abstract software architecture diagrams failed comprehension tests without a physical analogy.",
                occurrence_count=5
            ),
            MemoryRule(
                rule_id="RULE-GROUNDING-001",
                category="GROUNDING",
                directive="Explicitly state that RAG DOES NOT retrain the AI model or change its internal weights; it simply feeds reference notes into the prompt.",
                source_failure="Frequent beginner confusion assuming RAG is fine-tuning or training new models.",
                occurrence_count=4
            ),
            MemoryRule(
                rule_id="RULE-JARGON-001",
                category="JARGON",
                directive="Never use terms like 'Embeddings' or 'Vector DB' without first demystifying them as 'Search Numbers' or 'Library Catalog Cards'.",
                source_failure="Unexplained AI buzzwords caused high drop-off in reader comprehension checks.",
                occurrence_count=6
            )
        ]
        self.save()

    def save(self):
        try:
            with open(self.memory_file, "w", encoding="utf-8") as f:
                json.dump({"rules": [r.model_dump() for r in self.rules], "last_updated": datetime.now().isoformat()}, f, indent=2)
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(self.run_history, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to persist institutional memory ({e})")

    def get_guidelines_for_prompt(self) -> List[str]:
        """Format accumulated memory rules as actionable negative and positive guidelines."""
        return [f"[{r.category}] {r.directive} (Learned from {r.occurrence_count} past failure cases)" for r in self.rules]

    def learn_from_rejection(self, rejection: RejectionRecord):
        """
        Self-evolution engine: Inspects failed checkpoints and root cause from a rejection,
        synthesizing or sharpening institutional memory rules so the error is never repeated.
        """
        for failed in rejection.failed_checkpoints:
            matched_rule = next((r for r in self.rules if failed in r.source_failure or failed in r.category), None)
            if matched_rule:
                matched_rule.occurrence_count += 1
                matched_rule.directive = f"{matched_rule.directive} CRITICAL: Must avoid '{rejection.root_cause_analysis[:80]}'."
            else:
                category = "JARGON" if "JARGON" in failed else ("VOCABULARY" if "VOCAB" in failed else "GROUNDING")
                new_rule = MemoryRule(
                    rule_id=f"RULE-AUTO-{len(self.rules) + 1:03d}",
                    category=category,
                    directive=f"Guardrail against failure in '{failed}': {rejection.remedy_applied}",
                    source_failure=rejection.root_cause_analysis[:140],
                    occurrence_count=1
                )
                self.rules.append(new_rule)
        self.save()

    def record_run(self, run_summary: Dict[str, Any]):
        """Append full workflow run record to historical logs."""
        self.run_history.append(run_summary)
        self.save()

    def get_evolution_report(self) -> Dict[str, Any]:
        """Provides an analytics snapshot of how the system has self-evolved across runs."""
        total_runs = len(self.run_history)
        total_rejections = sum(len(r.get("rejection_history", [])) for r in self.run_history)
        rules_count = len(self.rules)
        return {
            "total_runs": total_runs,
            "total_rejections_caught_and_corrected": total_rejections,
            "active_guardrail_rules": rules_count,
            "top_rules": [r.model_dump() for r in sorted(self.rules, key=lambda x: x.occurrence_count, reverse=True)[:5]]
        }
