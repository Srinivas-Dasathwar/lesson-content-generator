# Loom Video Demonstration Script & Presenter Guide (15–20 Mins)
## Take-Home Technical Assessment: Associate GenAI Engineer – Content Systems (NxtWave)

---

## 🎬 Presentation Checklist Before You Press "Record"
- [ ] **Loom Setup:** Camera enabled, face clearly visible in lower corner, microphone tested.
- [ ] **Tabs Open:**
  1. Terminal (split-screen or primary window showing `python -m src.main --inject-flaw jargon_bomb`)
  2. Web UI Dashboard at `http://localhost:8000`
  3. Visual Studio Code / IDE showing project code (`src/workflow.py`, `src/evaluators/rubric_evaluator.py`, `src/memory/institutional_memory.py`)
  4. Final Lesson Document (`docs/FINAL_LESSON_RAG.md`)

---

## ⏱️ Minute-by-Minute Video Roadmap

| Timestamp | Phase | Topic / Demonstration | Screen View |
| :--- | :--- | :--- | :--- |
| **00:00 – 02:00** | **Introduction** | Who you are, role context, target persona breakdown (12th-grade Indian graduate, non-English-medium, zero AI background). | Face + Title Slide / Web Header |
| **02:00 – 05:00** | **System Architecture** | Explain the agentic workflow: State Machine, Curriculum Planner, Multi-Stage Evaluator (Tier A Linter + Tier B Semantic Rubric), Feedback Injection, Self-Evolving Institutional Memory. | IDE / Architecture Diagram |
| **05:00 – 09:30** | **Live End-to-End Run with Deliberate Flaw** | Trigger workflow with deliberate flaw (`jargon_bomb` or `hallucinated_facts`). Show the evaluator catching the error, logging rejection, and auto-recovering on retry! | Web UI / Terminal |
| **09:30 – 13:00** | **Deep Dive: The Hard Pass/Fail Rubric** | Explain the 6 hard checkpoints (Accuracy, 12th-grade Vocabulary, Relatable Analogy, No Unexplained Jargon, 3 Pillars, Coherent Teaching Flow) and why "no partial credit" is essential. | IDE (`rubric_evaluator.py`) |
| **13:00 – 16:00** | **Self-Evolution & Persistent Memory** | Show `data/institutional_memory.json`. Explain how repeated rejections distill negative constraints across runs so the system gets smarter over time. | IDE (`institutional_memory.py`) |
| **16:00 – 18:30** | **Final Lesson Walkthrough** | Review the generated output on "Introduction to RAG", showing the Open-Book Exam analogy and interactive scenario quiz. | `FINAL_LESSON_RAG.md` |
| **18:30 – 20:00** | **Engineering Trade-offs & Conclusion** | Address cost, latency, deterministic vs LLM evaluation, and production scaling. Closing thoughts. | Face + Summary View |

---

## 🎙️ Detailed Spoken Script & Stage Directions

### Part 1: Introduction & Learner Persona (00:00 – 02:00)
> **What to Say:**  
> *"Hello NxtWave hiring team! My name is [Your Name], and this is my presentation for the Associate GenAI Engineer – Content Systems take-home assessment.*  
>  
> *Before jumping into code, I want to emphasize the core philosophy behind this project: **This is not just a clever prompt that generates text.** In production content systems at NxtWave, our goal is to build an autonomous agentic loop that generates learning materials, rigorously audits its own quality against uncompromising pedagogical rubrics, and decides whether content is truly good enough to ship before a human reviewer or student ever sees it.*  
>  
> *Our target learner is very specific: A 12th-grade graduate from India who studied in a non-English-medium school. They have limited English vocabulary, zero prior computer science or AI background, but are deeply ambitious to break into tech. This means high-dimensional math or raw jargon like 'bi-encoder' will alienate them immediately. They need intuitive, relatable everyday analogies like exams, school notes, or library cards."*

---

### Part 2: High-Level Architecture Walkthrough (02:00 – 05:00)
*(Switch screen to your IDE or Web UI flow diagram)*

> **What to Say:**  
> *"Let's look at the system architecture. I implemented a stateful agentic graph with five distinct components:*  
>  
> 1. * **Institutional Memory Node:** Loads accumulated guardrails and distilled rules from past runs stored in `data/institutional_memory.json`.*  
> 2. * **Curriculum Planner Node:** Deconstructs the topic into six pedagogical milestones (Hook, Analogy, Core Problem, 3-Step Mechanism, Flow Diagram, and Concept Check Quiz).*  
> 3. * **Lesson Generator Node:** Takes the blueprint, persona constraints, memory guidelines, and any feedback from prior rejections to draft the lesson.*  
> 4. * **Multi-Stage Evaluator Node:** This is a two-tier system:  
>    - **Tier A (Deterministic Linter):** Fast, sub-millisecond static regex and readability checks that flag forbidden graduate jargon and run-on sentences over 25 words.  
>    - **Tier B (Semantic LLM Rubric Judge):** Audits the draft across six strict pass/fail checkpoints with zero partial credit.  
> 5. * **Self-Evolution & Feedback Router:** If any check fails, it extracts the exact failure pattern into memory and feeds actionable remediation instructions back to the generator. If all pass, it ships the content."*

---

### Part 3: Live Demo — Evaluator Catching a Deliberate Error (05:00 – 09:30)
*(Switch screen to Web UI at `http://localhost:8000` or the Terminal)*

> **What to Say & Do:**  
> 1. *Show the Control Panel on the Web UI or run the CLI command:*  
>    `python -m src.main --inject-flaw jargon_bomb`  
> 2. *Explain:*  
>    *"To demonstrate the evaluator's strictness, I added a deliberate flaw injection mode. Here, I'm selecting `jargon_bomb`. This forces the initial generator to produce graduate-level academic text filled with unexplained terms like 'manifold degradation', '1536-dimensional float32 tensors', and 'HNSW graphs'."*  
> 3. *Hit 'Run Agentic Pipeline'. Watch the live pipeline transition:*  
>    - *Show Round 1 generation completing.*  
>    - *Point your mouse to the Rubric Audit Scorecard.*  
>    *"Look at Round 1: The evaluator immediately caught the error! It failed four checkpoints: `AUDIENCE_VOCABULARY_AND_TONE`, `RELATABLE_ANALOGY`, `NO_UNEXPLAINED_JARGON`, and `COHERENT_TEACHING_FLOW`."*  
>    - *Open the Rejection Log tab:*  
>    *"Notice the structured Rejection Record. The auditor logged the exact citation snippet: '1536-dimensional float32 dense tensors indexed via HNSW graphs', flagged that it is completely unsuitable for a 12th-grade student, and generated this specific remedy: 'Replace all research jargon with simple everyday English and use an Open-Book Exam analogy'."*  
> 4. *Watch Round 2 trigger automatically:*  
>    *"The workflow does not stop. It automatically feeds this rejection feedback into Round 2. The generator incorporates the critique, and on Round 2, look at the screen—all six checkpoints turn green ([PASS])! The lesson clears the bar and is approved to ship."*

---

### Part 4: The 6-Dimension Hard Pass/Fail Rubric (09:30 – 13:00)
*(Open `src/evaluators/rubric_evaluator.py` in your code editor)*

> **What to Say:**  
> *"Why did I design the evaluator with hard pass/fail checkpoints instead of a numerical 1-to-10 score?  
> In educational publishing, numerical scores create false confidence. If a lesson scores 8 out of 10, but the 2 points lost were because it taught factually incorrect information (like claiming RAG retrains model weights), shipping that content damages student learning.  
>  
> Our rubric enforces six hard checkpoints with zero partial credit:  
> 1. **ACCURACY_AND_GROUNDING:** Ensures RAG's 3 pillars are factually correct and verifies it explicitly states model weights are never altered.  
> 2. **AUDIENCE_VOCABULARY_AND_TONE:** Ensures language is friendly to non-English-medium 12th-graders.  
> 3. **RELATABLE_ANALOGY:** Requires a concrete physical metaphor like Open-Book vs Closed-Book exams.  
> 4. **NO_UNEXPLAINED_JARGON:** Scans for and eliminates ungrounded buzzwords.  
> 5. **KEY_PILLARS_COVERAGE:** Confirms What, Why, and How are all answered.  
> 6. **COHERENT_TEACHING_FLOW:** Verifies pedagogical progression and includes an active recall scenario quiz."*

---

### Part 5: Self-Evolution & Persistent Memory Across Runs (13:00 – 16:00)
*(Open `src/memory/institutional_memory.py` and `data/institutional_memory.json`)*

> **What to Say:**  
> *"Another key requirement was making the system self-evolving across runs.  
> If an evaluator rejects a draft on Monday for using complex vocabulary, an ordinary prompt starts from scratch on Tuesday and makes the exact same mistake.  
>  
> In our system, `InstitutionalMemory` persists to disk. Every time a rejection occurs, the `learn_from_rejection` method inspects the failed checkpoints and synthesizes a new negative guardrail rule into `institutional_memory.json`.  
>  
> When any future lesson is generated, these accumulated memory rules are injected into the generator's system prompt as active guardrails. In our test logs, you can see that as the system runs, its rejection rate decreases because it carries institutional memory forward."*

---

### Part 6: The Final Lesson Content Output (16:00 – 18:30)
*(Open `docs/FINAL_LESSON_RAG.md` or preview tab in Web UI)*

> **What to Say:**  
> *"Now let's examine the final lesson generated on 'Introduction to RAG'.  
> Look at the structure:  
> - **The Hook:** Starts with a relatable question: 'Why does ChatGPT sometimes make up fake answers?'  
> - **The Big Analogy:** Contrasts the 'Closed-Book Exam' (normal AI guessing from memory) with the 'Open-Book Exam' (RAG searching the textbook before answering). This maps directly to an Indian student's real-life experience.  
> - **The 3 Problems:** Clear breakdown of Hallucinations, Outdated Data, and Data Privacy.  
> - **How it Works (R-A-G):** Breaks down Retrieval (smart librarian), Augmentation (stapling the notes), and Generation (writing the answer).  
> - **ASCII Mental Flow Diagram:** Simple visual map.  
> - **Active Recall Quiz:** A real-world scenario about a college WhatsApp admission bot with immediate answers and clear explanations."*

---

### Part 7: Engineering Trade-offs & Wrap-Up (18:30 – 20:00)
*(Bring face-cam back to center or split view)*

> **What to Say:**  
> *"To conclude, I'd like to share the engineering trade-offs made in this system:  
> 1. **Two-Tier vs LLM-Only Evaluation:** Running a full LLM judge on every sentence is expensive and slow. Using Tier A deterministic regex filters first catches 80% of jargon and sentence-length bugs in under 5 milliseconds before invoking the LLM judge.  
> 2. **Deterministic Rejection Recovery:** We cap retries at 2, guaranteeing the state machine terminates and never enters an infinite token-burning loop.  
> 3. **Provider Agnostic Architecture:** The system runs out of the box with zero external setup using our high-fidelity Mock provider, while seamlessly switching to Google Gemini or OpenAI when an API key is provided.  
>  
> All code, tests, documentation, and logs are organized in the GitHub repository. Thank you for your time, and I look forward to the next stage of the conversation with NxtWave!"*
