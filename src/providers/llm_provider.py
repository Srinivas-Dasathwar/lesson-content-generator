"""
LLM Provider Abstraction layer supporting Gemini, OpenAI/Groq, and a High-Fidelity Mock Provider.
"""

import os
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class BaseLLMProvider(ABC):
    @abstractmethod
    def generate_text(self, prompt: str, system_prompt: Optional[str] = None, temperature: float = 0.7) -> str:
        """Generate raw text response from the LLM."""
        pass

    @abstractmethod
    def generate_json(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """Generate structured JSON response from the LLM."""
        pass


class MockLLMProvider(BaseLLMProvider):
    """
    High-fidelity deterministic LLM simulator.
    Simulates deliberate flaws on demand or initial generation, and fixes them accurately
    upon receiving rubric feedback, demonstrating the full agentic loop reliably.
    """

    def __init__(self, simulate_flaw_on_first_try: bool = False, flaw_type: str = "none"):
        self.simulate_flaw_on_first_try = simulate_flaw_on_first_try
        self.flaw_type = flaw_type
        self.call_count = 0

    def generate_text(self, prompt: str, system_prompt: Optional[str] = None, temperature: float = 0.7) -> str:
        self.call_count += 1
        return self._craft_mock_response(prompt)

    def generate_json(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        self.call_count += 1
        text = self._craft_mock_response(prompt)
        # Attempt to parse json from text
        try:
            # Extract json if enclosed in markdown blocks
            clean_text = text.strip()
            if "```json" in clean_text:
                clean_text = clean_text.split("```json")[1].split("```")[0].strip()
            elif "```" in clean_text:
                clean_text = clean_text.split("```")[1].split("```")[0].strip()
            return json.loads(clean_text)
        except Exception:
            return {"raw": text}

    def _craft_mock_response(self, prompt: str) -> str:
        # Check if this is an evaluation prompt
        if "Evaluate the following lesson draft" in prompt or "EVALUATION_TASK" in prompt:
            return self._mock_evaluation(prompt)

        # Check if this is a curriculum planning prompt
        if "CURRICULUM_PLANNING_TASK" in prompt:
            return self._mock_curriculum_plan()

        # Check if this is a generation prompt
        return self._mock_generation(prompt)

    def _mock_curriculum_plan(self) -> str:
        return json.dumps({
            "topic": "RAG (Retrieval-Augmented Generation)",
            "hook": "Why does ChatGPT sometimes give confident but wrong answers, or say 'I don't know' about today's news?",
            "analogy": "Open-book exam vs Closed-book exam: Remembering everything vs having your textbook on the table to check before answering.",
            "the_problem": "Plain AI relies only on memory frozen in training. It cannot read your personal files or current live facts.",
            "rag_definition": "RAG = Retrieval (Search) + Augmentation (Add to prompt) + Generation (Answer with proof).",
            "step_by_step": [
                "Step 1: Convert documents into easy-to-search chunks.",
                "Step 2: When student asks a question, search and fetch relevant snippets.",
                "Step 3: Hand the snippets to the AI with instruction: Answer only using these facts."
            ],
            "quiz_question": "If an AI gives an outdated answer about the 2026 cricket match, how does RAG solve this?",
            "summary": "RAG makes AI reliable by giving it an open notebook to read before it speaks."
        }, indent=2)

    def _mock_generation(self, prompt: str) -> str:
        # If flaw injection is active and this is iteration 0 (no feedback yet)
        is_retry = "PREVIOUS REJECTION FEEDBACK" in prompt or "FEEDBACK FROM EVALUATOR" in prompt

        if not is_retry and self.flaw_type == "jargon_bomb":
            return json.dumps({
                "topic": "RAG (Retrieval-Augmented Generation)",
                "title": "Introduction to Retrieval-Augmented Generation with Dense Vector Embeddings",
                "hook": "Modern deep generative transformers suffer from hallucinations due to high-dimensional latent space manifold degradation.",
                "everyday_analogy": "Imagine a high-dimensional Euclidean vector space where cosine similarity metrics determine k-nearest neighbor retrieval indices.",
                "problem_statement": "Parametric memory limitations restrict autoregressive probabilistic token sampling from accessing non-parametric external corpus stores without backpropagation.",
                "how_it_works": "First, the bi-encoder tokenizes the corpus into 1536-dimensional float32 dense tensors indexed via Hierarchical Navigable Small World (HNSW) graphs. Next, semantic similarity scoring executes via dot-product computation, followed by top-k beam search synthesis.",
                "mental_model_diagram": "Corpus -> [Bi-Encoder Transformer] -> Dense Vector Space -> HNSW Index -> Top-K Nearest Neighbors -> Cross-Attention Decoder.",
                "concept_check_quiz": "Question: What is the computational complexity of exact k-NN vs approximate HNSW vector retrieval?\nA) O(N*d) vs O(log N)\nB) O(1)\nC) O(N^2)\nCorrect Answer: A.",
                "summary_and_next_steps": "RAG replaces static fine-tuning with dynamic non-parametric retrieval. Next lesson: Contrastive Loss Optimization."
            }, indent=2)

        if not is_retry and self.flaw_type == "hallucinated_facts":
            return json.dumps({
                "topic": "RAG (Retrieval-Augmented Generation)",
                "title": "Understanding RAG: The AI Model Retraining System",
                "hook": "Have you ever wanted an AI that learns everything new instantly?",
                "everyday_analogy": "It's like retraining your brain every single second.",
                "problem_statement": "AI models are slow because they do not retrain their weights when you type a prompt.",
                "how_it_works": "Every time you ask a question, RAG takes your PDF, calculates gradient descent backpropagation, permanently updates the weights of the AI model on your computer, and saves a brand new fine-tuned model checkpoint.",
                "mental_model_diagram": "Your PDF -> Gradient Descent -> Update Neural Weights -> Brand New Model -> Answer.",
                "concept_check_quiz": "Question: Does RAG modify the permanent model weights during query time?\nA) Yes, it runs backpropagation on every prompt\nB) No\nCorrect Answer: A.",
                "summary_and_next_steps": "RAG retrains models continuously on the fly."
            }, indent=2)

        if not is_retry and self.flaw_type == "missing_analogy":
            return json.dumps({
                "topic": "RAG (Retrieval-Augmented Generation)",
                "title": "Technical Overview of Retrieval-Augmented Generation",
                "hook": "RAG is a technique in modern artificial intelligence systems.",
                "everyday_analogy": "There is no simple real-world comparison for such advanced mathematical software algorithms.",
                "problem_statement": "Large language models only know what they saw during initial training phases.",
                "how_it_works": "The retrieval engine searches a database. The found data is placed in the context window. The language model produces text based on the combined prompt.",
                "mental_model_diagram": "Query + DB -> Context -> LLM -> Text",
                "concept_check_quiz": "Question: What does RAG stand for?\nA) Retrieval-Augmented Generation\nB) Rapid Action Group\nCorrect Answer: A.",
                "summary_and_next_steps": "Now you know what RAG stands for."
            }, indent=2)

        # Passing High-Quality Lesson (Tailored specifically for 12th-grade non-English-medium Indian student)
        return json.dumps({
            "topic": "RAG (Retrieval-Augmented Generation)",
            "title": "Supercharge AI with RAG: The 'Open-Book Exam' Secret for Computers",
            "hook": "Imagine you have an important exam tomorrow. If the teacher says, 'You cannot bring any books, answer only from your memory!' that is scary, right? You might forget dates or confuse formulas. But what if the teacher says, 'You can keep your textbook on the desk. First search the page, read the exact lines, and then write your answer!' Suddenly, you will not guess or make silly mistakes. This simple trick is called RAG in the AI world!",
            "everyday_analogy": "Think of an Open-Book Exam vs a Closed-Book Exam.\n- A normal AI like ChatGPT without RAG is like a student writing a **Closed-Book Exam**. It has to remember everything from its past training. If you ask about something new or private (like your college fee receipt), it has to guess or say 'I don't know'.\n- An AI with **RAG** is like that same smart student writing an **Open-Book Exam**. It has a library desk in front of it. Before answering your question, it walks to the bookshelf, finds the exact 2 pages with the answer, reads them carefully, and writes a perfect, truthful answer for you!",
            "problem_statement": "Why do we desperately need RAG in India's growing AI industry?\n1. **AI Hallucinations (Confidently Making Up False Facts):** When an AI doesn't know an answer, it doesn't stay quiet; it often creates fake stories that sound real.\n2. **Outdated Knowledge:** An AI trained in 2024 does not know about today's cricket match score or today's government job circular.\n3. **Private Data Privacy:** A hospital or bank cannot send their secret customer records to train a huge global AI model from scratch. It is too risky and costs crores of rupees!",
            "how_it_works": "RAG solves this in 3 simple English steps that anyone can remember:\n\n1. **R stands for RETRIEVAL (Search & Fetch):**\n   When you type a question (e.g., 'What is the last date for JEE Mains application?'), the system does NOT ask the AI to guess from memory. Instead, it instantly acts like a smart librarian: it scans your documents, notes, or website to find the exact 2 or 3 sentences that contain the answer.\n\n2. **A stands for AUGMENTATION (Add Reference Notes):**\n   'Augment' simply means 'to add or enrich'. The system takes your original question and staples the fresh facts found in Step 1 right on top of it. It creates a message like: *'Hey AI, here is the official government notice: [JEE registration ends on Nov 30]. Now answer the student question using ONLY this notice.'*\n\n3. **G stands for GENERATION (Polite Clear Answer):**\n   Now the AI reads the clean notes and writes a warm, fluent answer in simple English. It doesn't need to guess, because the verified truth is right in front of its eyes!",
            "mental_model_diagram": "```\n[Student Question] ──────────┐\n                            ▼\n               [Step 1: RETRIEVAL]\n               Librarian searches your PDF/Notes\n               Extracts: \"Exact Proof Sentences\"\n                            │\n                            ▼\n               [Step 2: AUGMENTATION]\n               Staple Question + Proof Sentences together\n                            │\n                            ▼\n               [Step 3: GENERATION]\n               AI writes clean, 100% truthful answer!\n```",
            "concept_check_quiz": "Let's check your understanding with a quick 1-minute question!\n\n**Question:** A college builds a WhatsApp chatbot for new 12th-pass admissions. When a student asks, 'What is the hostel mess fee for 2026?', what will a RAG system do?\n\nA) Retrain the entire AI model overnight with new weights.\nB) First search the 2026 college fee PDF, attach the fee paragraph to the prompt, and then let the AI write the answer.\nC) Make the AI guess based on fees from other colleges in America.\n\n**Correct Answer: B**\n*Explanation:* Perfect! RAG never retrains the big AI model. It simply fetches the exact hostel fee paragraph from the college PDF (Retrieval) and hands it to the AI to write a helpful reply (Augment + Generate).",
            "summary_and_next_steps": "Key Takeaways to Remember:\n1. RAG = Retrieval (Search) + Augmentation (Add Notes) + Generation (Write Answer).\n2. It turns a risky closed-book AI into a reliable open-book assistant.\n3. It stops fake answers (hallucinations) without spending millions of rupees on retraining.\n\n**Next Step in Your AI Journey:** Next, we will see how computers convert words into 'Search Numbers' (called Embeddings) to find pages in less than a second!"
        }, indent=2)

    def _mock_evaluation(self, prompt: str) -> str:
        # Check if the text being evaluated contains deliberate flaws
        is_jargon = "manifold degradation" in prompt or "HNSW" in prompt or "1536-dimensional" in prompt
        is_hallucination = "permanently updates the weights" in prompt or "gradient descent" in prompt
        is_missing_analogy = "no simple real-world comparison" in prompt

        if is_jargon:
            return json.dumps({
                "overall_passed": False,
                "summary": "REJECTED: The lesson draft contains overwhelming, unexplained graduate-level technical jargon completely unsuitable for a 12th-grade graduate with basic English.",
                "checkpoints": [
                    {
                        "checkpoint_id": "ACCURACY_AND_GROUNDING",
                        "dimension_name": "Accurate & Grounded",
                        "passed": True,
                        "score_desc": "PASS",
                        "critique": "The technical terminology is accurate from a theoretical computer science perspective, but improperly positioned.",
                        "snippet_citation": "HNSW graphs, cosine similarity",
                        "actionable_remedy": "Maintain factual accuracy but simplify."
                    },
                    {
                        "checkpoint_id": "AUDIENCE_VOCABULARY_AND_TONE",
                        "dimension_name": "Beginner-Friendly Language (12th Grade India)",
                        "passed": False,
                        "score_desc": "FAIL",
                        "critique": "Violates the audience constraint. Uses dense mathematical and research vocabulary like 'manifold degradation', 'Euclidean', 'non-parametric'.",
                        "snippet_citation": "Modern deep generative transformers suffer from hallucinations due to high-dimensional latent space manifold degradation.",
                        "actionable_remedy": "Replace all research jargon with simple, everyday 12th-grade English. Use short sentences (under 20 words)."
                    },
                    {
                        "checkpoint_id": "RELATABLE_ANALOGY",
                        "dimension_name": "Teaches by Relatable Example/Analogy",
                        "passed": False,
                        "score_desc": "FAIL",
                        "critique": "The analogy uses 'high-dimensional Euclidean vector space' which is not an everyday analogy.",
                        "snippet_citation": "Imagine a high-dimensional Euclidean vector space...",
                        "actionable_remedy": "Use an everyday Indian life analogy, such as an Open-Book Examination vs Closed-Book Exam or a school library."
                    },
                    {
                        "checkpoint_id": "NO_UNEXPLAINED_JARGON",
                        "dimension_name": "Clear, No Unexplained Jargon",
                        "passed": False,
                        "score_desc": "FAIL",
                        "critique": "Fails hard pass/fail. Unexplained terms: HNSW, Bi-encoder, Cosine similarity, beam search.",
                        "snippet_citation": "1536-dimensional float32 dense tensors indexed via Hierarchical Navigable Small World (HNSW) graphs.",
                        "actionable_remedy": "Do not mention HNSW or tensor dimensions. Focus strictly on Retrieval (Search), Augment (Attach), Generate (Answer)."
                    },
                    {
                        "checkpoint_id": "CORE_PILLARS_COVERAGE",
                        "dimension_name": "Covers Key Points (What, Why, How)",
                        "passed": True,
                        "score_desc": "PASS",
                        "critique": "Covers what and how, though in an impenetrable fashion.",
                        "snippet_citation": "How it works: bi-encoder tokenizes...",
                        "actionable_remedy": "Keep the What, Why, How structure but make it conversational."
                    },
                    {
                        "checkpoint_id": "COHERENT_TEACHING_FLOW",
                        "dimension_name": "Coherent Pedagogical Flow & Concept Check",
                        "passed": False,
                        "score_desc": "FAIL",
                        "critique": "Quiz tests algorithmic time complexity O(N*d) vs O(log N), which is impossible for a beginner.",
                        "snippet_citation": "Question: What is the computational complexity of exact k-NN vs approximate HNSW vector retrieval?",
                        "actionable_remedy": "Replace quiz with an intuitive scenario-based question (e.g. college WhatsApp admission bot or exam notes)."
                    }
                ]
            }, indent=2)

        if is_hallucination:
            return json.dumps({
                "overall_passed": False,
                "summary": "REJECTED: Severe technical hallucination. The lesson states that RAG retrains model weights via gradient descent backpropagation, which is factually incorrect and misinforms learners.",
                "checkpoints": [
                    {
                        "checkpoint_id": "ACCURACY_AND_GROUNDING",
                        "dimension_name": "Accurate & Grounded",
                        "passed": False,
                        "score_desc": "FAIL",
                        "critique": "Fatal technical error: RAG explicitly does NOT retrain or fine-tune neural model weights at query time. It injects context into the prompt.",
                        "snippet_citation": "Every time you ask a question, RAG takes your PDF, calculates gradient descent backpropagation, permanently updates the weights of the AI model...",
                        "actionable_remedy": "Correct the factual error: Clarify that RAG never touches the AI's internal model weights. It only looks up reference text and feeds it as a prompt."
                    },
                    {
                        "checkpoint_id": "AUDIENCE_VOCABULARY_AND_TONE",
                        "dimension_name": "Beginner-Friendly Language (12th Grade India)",
                        "passed": True,
                        "score_desc": "PASS",
                        "critique": "Language is relatively simple, but conveying wrong information.",
                        "snippet_citation": None,
                        "actionable_remedy": None
                    },
                    {
                        "checkpoint_id": "RELATABLE_ANALOGY",
                        "dimension_name": "Teaches by Relatable Example/Analogy",
                        "passed": False,
                        "score_desc": "FAIL",
                        "critique": "Analogy of 'retraining your brain every single second' reinforces the false claim.",
                        "snippet_citation": "It's like retraining your brain every single second.",
                        "actionable_remedy": "Use an Open-Book exam analogy: you don't grow a new brain, you simply look at your notebook."
                    },
                    {
                        "checkpoint_id": "NO_UNEXPLAINED_JARGON",
                        "dimension_name": "Clear, No Unexplained Jargon",
                        "passed": False,
                        "score_desc": "FAIL",
                        "critique": "Uses terms like 'gradient descent backpropagation' and 'fine-tuned model checkpoint' without explanation.",
                        "snippet_citation": "calculates gradient descent backpropagation",
                        "actionable_remedy": "Remove backpropagation and gradient descent; explain that the AI model remains frozen."
                    },
                    {
                        "checkpoint_id": "CORE_PILLARS_COVERAGE",
                        "dimension_name": "Covers Key Points (What, Why, How)",
                        "passed": False,
                        "score_desc": "FAIL",
                        "critique": "Fails because the 'How' is completely inaccurate.",
                        "snippet_citation": "Update Neural Weights -> Brand New Model",
                        "actionable_remedy": "Explain the 3 real pillars: Retrieve (search), Augment (attach), Generate (synthesize)."
                    },
                    {
                        "checkpoint_id": "COHERENT_TEACHING_FLOW",
                        "dimension_name": "Coherent Pedagogical Flow & Concept Check",
                        "passed": False,
                        "score_desc": "FAIL",
                        "critique": "The quiz tests the learner on a false premise.",
                        "snippet_citation": "Question: Does RAG modify the permanent model weights during query time?",
                        "actionable_remedy": "Update quiz to test understanding of the search-and-attach mechanism."
                    }
                ]
            }, indent=2)

        # Standard Passing Evaluation
        return json.dumps({
            "overall_passed": True,
            "summary": "APPROVED: All 6 rubric checkpoints passed with distinction. Lesson is exceptionally tailored to a 12th-grade Indian student, crystal clear, accurate, and ready to ship.",
            "checkpoints": [
                {
                    "checkpoint_id": "ACCURACY_AND_GROUNDING",
                    "dimension_name": "Accurate & Grounded",
                    "passed": True,
                    "score_desc": "PASS",
                    "critique": "The 3 pillars (Retrieve, Augment, Generate) are technically accurate, highlighting that model weights are not modified.",
                    "snippet_citation": "RAG never retrains the big AI model. It simply fetches the exact hostel fee paragraph from the college PDF (Retrieval) and hands it to the AI...",
                    "actionable_remedy": None
                },
                {
                    "checkpoint_id": "AUDIENCE_VOCABULARY_AND_TONE",
                    "dimension_name": "Beginner-Friendly Language (12th Grade India)",
                    "passed": True,
                    "score_desc": "PASS",
                    "critique": "Vocabulary is warm, accessible, and uses simple sentences suitable for learners from non-English-medium schools.",
                    "snippet_citation": "Think of an Open-Book Exam vs a Closed-Book Exam... Suddenly, you will not guess or make silly mistakes.",
                    "actionable_remedy": None
                },
                {
                    "checkpoint_id": "RELATABLE_ANALOGY",
                    "dimension_name": "Teaches by Relatable Example/Analogy",
                    "passed": True,
                    "score_desc": "PASS",
                    "critique": "The Open-Book vs Closed-Book examination analogy is intuitive, culturally resonant for Indian students, and maps 1:1 to RAG mechanics.",
                    "snippet_citation": "A normal AI like ChatGPT without RAG is like a student writing a Closed-Book Exam... An AI with RAG is like that same smart student writing an Open-Book Exam.",
                    "actionable_remedy": None
                },
                {
                    "checkpoint_id": "NO_UNEXPLAINED_JARGON",
                    "dimension_name": "Clear, No Unexplained Jargon",
                    "passed": True,
                    "score_desc": "PASS",
                    "critique": "Every term (Hallucination, Retrieval, Augment, Generation) is explained in plain words before use. No intimidating math.",
                    "snippet_citation": "'Augment' simply means 'to add or enrich'. The system takes your original question and staples the fresh facts...",
                    "actionable_remedy": None
                },
                {
                    "checkpoint_id": "CORE_PILLARS_COVERAGE",
                    "dimension_name": "Covers Key Points (What, Why, How)",
                    "passed": True,
                    "score_desc": "PASS",
                    "critique": "Comprehensive coverage of What it is, Why it matters (hallucinations, privacy, cost), and How it works step-by-step.",
                    "snippet_citation": "Why do we desperately need RAG in India's growing AI industry?... RAG solves this in 3 simple English steps...",
                    "actionable_remedy": None
                },
                {
                    "checkpoint_id": "COHERENT_TEACHING_FLOW",
                    "dimension_name": "Coherent Pedagogical Flow & Concept Check",
                    "passed": True,
                    "score_desc": "PASS",
                    "critique": "Pedagogical flow progresses seamlessly from Hook -> Analogy -> Problem -> Solution -> Flow Diagram -> Scenario Quiz -> Takeaway.",
                    "snippet_citation": "Let's check your understanding with a quick 1-minute question!... Question: A college builds a WhatsApp chatbot for new 12th-pass admissions...",
                    "actionable_remedy": None
                }
            ]
        }, indent=2)


class GeminiProvider(BaseLLMProvider):
    """
    Direct REST integration with Google Gemini API using httpx.
    Requires GEMINI_API_KEY or GOOGLE_API_KEY environment variable.
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-2.5-flash"):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY environment variable is required.")
        self.model = model
        self.endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"

    def generate_text(self, prompt: str, system_prompt: Optional[str] = None, temperature: float = 0.7) -> str:
        import httpx
        contents = []
        if system_prompt:
            contents.append({"role": "user", "parts": [{"text": f"SYSTEM INSTRUCTIONS:\n{system_prompt}"}]})
            contents.append({"role": "model", "parts": [{"text": "Understood. I will strictly adhere to these instructions."}]})
        contents.append({"role": "user", "parts": [{"text": prompt}]})

        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": 4096
            }
        }

        with httpx.Client(timeout=60.0) as client:
            resp = client.post(self.endpoint, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]

    def generate_json(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        text = self.generate_text(
            prompt + "\n\nCRITICAL: Respond ONLY with valid, raw JSON (no conversational preamble, no markdown backticks unless required).",
            system_prompt=system_prompt,
            temperature=0.2
        )
        clean_text = text.strip()
        if "```json" in clean_text:
            clean_text = clean_text.split("```json")[1].split("```")[0].strip()
        elif "```" in clean_text:
            clean_text = clean_text.split("```")[1].split("```")[0].strip()
        return json.loads(clean_text)


class OpenAIProvider(BaseLLMProvider):
    """
    Generic OpenAI-compatible provider (OpenAI, Groq, Ollama, DeepSeek).
    """

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, model: str = "gpt-4o-mini"):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY") or os.environ.get("GROQ_API_KEY") or "dummy"
        self.base_url = base_url or os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.model = model

    def generate_text(self, prompt: str, system_prompt: Optional[str] = None, temperature: float = 0.7) -> str:
        import httpx
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature
        }

        with httpx.Client(timeout=60.0) as client:
            resp = client.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    def generate_json(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        text = self.generate_text(
            prompt + "\n\nCRITICAL: Respond ONLY with valid JSON.",
            system_prompt=system_prompt,
            temperature=0.2
        )
        clean_text = text.strip()
        if "```json" in clean_text:
            clean_text = clean_text.split("```json")[1].split("```")[0].strip()
        elif "```" in clean_text:
            clean_text = clean_text.split("```")[1].split("```")[0].strip()
        return json.loads(clean_text)


def get_llm_provider(
    provider_name: str = "auto",
    flaw_type: str = "none"
) -> BaseLLMProvider:
    """
    Factory function to instantiate the appropriate LLM provider.
    Defaults to auto-detecting keys; falls back to High-Fidelity MockProvider.
    """
    if provider_name == "gemini" or (provider_name == "auto" and (os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"))):
        try:
            return GeminiProvider()
        except Exception as e:
            logger.warning(f"Could not initialize GeminiProvider ({e}). Falling back to MockLLMProvider.")

    if provider_name == "openai" or (provider_name == "auto" and os.environ.get("OPENAI_API_KEY")):
        try:
            return OpenAIProvider()
        except Exception as e:
            logger.warning(f"Could not initialize OpenAIProvider ({e}). Falling back to MockLLMProvider.")

    if provider_name == "groq" or (provider_name == "auto" and os.environ.get("GROQ_API_KEY")):
        try:
            return OpenAIProvider(base_url="https://api.groq.com/openai/v1", model="llama-3.3-70b-versatile")
        except Exception as e:
            logger.warning(f"Could not initialize GroqProvider ({e}). Falling back to MockLLMProvider.")

    # High-fidelity mock simulator for reliable demonstration & zero-config testing
    return MockLLMProvider(simulate_flaw_on_first_try=(flaw_type != "none"), flaw_type=flaw_type)
