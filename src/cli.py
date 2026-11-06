"""
Rich Interactive CLI Interface for the Self-Evaluating Lesson Content Generator.
Provides live status panels, colored rubric scorecards, rejection diagnostics, and file export.
Windows CP1252/UTF-8 safe.
"""

import os
import sys
import argparse

# Ensure UTF-8 output encoding on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.markdown import Markdown
from src.workflow import LessonGeneratorWorkflow
from src.providers.llm_provider import get_llm_provider
from src.memory.institutional_memory import InstitutionalMemory

console = Console(safe_box=True)


def print_banner():
    banner_text = """
================================================================================
             AUTONOMOUS SELF-EVALUATING LESSON CONTENT GENERATOR
  Generate  ->  Evaluate (Hard Pass/Fail)  ->  Regenerate Loop  ->  Ship
================================================================================
"""
    console.print(banner_text, style="bold cyan")


def display_rubric_card(eval_result, iteration: int):
    table = Table(
        title=f"Rubric Evaluation Audit (Round {iteration + 1})",
        show_header=True,
        header_style="bold magenta",
        safe_box=True
    )
    table.add_column("Checkpoint Dimension", style="cyan", width=36)
    table.add_column("Result", justify="center", width=10)
    table.add_column("Auditor Critique & Citation Snippet", style="white")

    for cp in eval_result.checkpoints:
        status_text = Text("[PASS]", style="bold green") if cp.passed else Text("[FAIL]", style="bold red")
        critique_text = cp.critique
        if cp.snippet_citation:
            critique_text += f"\nSnippet: \"{cp.snippet_citation[:90]}...\""
        if not cp.passed and cp.actionable_remedy:
            critique_text += f"\nRemedy: {cp.actionable_remedy}"
        table.add_row(cp.dimension_name, status_text, critique_text)

    console.print(table)

    if eval_result.overall_passed:
        console.print(Panel(f"[bold green][PASS] LESSON APPROVED FOR SHIPPING![/bold green]\n{eval_result.summary}", border_style="green", safe_box=True))
    else:
        console.print(Panel(f"[bold red][FAIL] LESSON REJECTED - FAILS QUALITY THRESHOLD[/bold red]\n{eval_result.summary}\n[yellow]Triggering autonomous regeneration loop with targeted remedial feedback...[/yellow]", border_style="red", safe_box=True))


def display_rejection_history(rejections):
    if not rejections:
        console.print("[green]Zero rejections occurred in this run. Lesson passed on first try![/green]")
        return

    table = Table(title="Institutional Rejection & Diff Audit Log", show_header=True, header_style="bold yellow", safe_box=True)
    table.add_column("Round", justify="center", width=8)
    table.add_column("Failed Checkpoints", style="red", width=32)
    table.add_column("Root Cause & Feedback Injected to Prompt", style="white")

    for r in rejections:
        table.add_row(
            f"Round {r.iteration + 1}",
            "\n".join([f"- {f}" for f in r.failed_checkpoints]),
            f"[bold]Root Cause:[/bold] {r.root_cause_analysis}\n[bold yellow]Remedy Applied:[/bold yellow] {r.remedy_applied}"
        )
    console.print(table)


def main():
    parser = argparse.ArgumentParser(description="Autonomous Self-Evaluating Lesson Content Generator")
    parser.add_argument("--topic", type=str, default="RAG (Retrieval-Augmented Generation)", help="Topic for beginner lesson")
    parser.add_argument("--inject-flaw", type=str, choices=["none", "jargon_bomb", "hallucinated_facts", "missing_analogy"], default="none", help="Inject deliberate error to test evaluator catching & recovery")
    parser.add_argument("--provider", type=str, choices=["auto", "gemini", "openai", "groq", "mock"], default="auto", help="LLM Provider backend")
    parser.add_argument("--max-retries", type=int, default=2, help="Max retry regenerations before terminal state")
    parser.add_argument("--output-dir", type=str, default="docs", help="Directory to save final deliverables")
    parser.add_argument("--preview", action="store_true", help="Print full final markdown lesson to console")

    args = parser.parse_args()
    print_banner()

    console.print(f"[bold blue]Target Audience:[/bold blue] 12th-grade Indian graduate (non-English medium, zero AI knowledge)")
    console.print(f"[bold blue]Topic:[/bold blue] {args.topic}")
    console.print(f"[bold blue]Flaw Injection Mode:[/bold blue] [bold red]{args.inject_flaw}[/bold red]" if args.inject_flaw != "none" else "[bold green]None (Standard Mode)[/bold green]")
    console.print(f"[bold blue]Provider:[/bold blue] {args.provider}")
    console.print()

    # Initialize Provider and Workflow
    llm = get_llm_provider(provider_name=args.provider, flaw_type=args.inject_flaw)
    memory = InstitutionalMemory()
    workflow = LessonGeneratorWorkflow(llm_provider=llm, memory=memory, max_retries=args.max_retries)

    console.print("[cyan]Executing Agentic Workflow Loop...[/cyan]\n")

    def cli_progress(stage: str, data: dict):
        if stage == "MEMORY_LOADED":
            console.print(f"[cyan]Brain: Institutional Memory: Loaded {len(data.get('rules', []))} guardrail directives from data/institutional_memory.json[/cyan]")
        elif stage == "PLAN_CREATED":
            console.print(f"[green]Curriculum Plan Blueprint established.[/green]")
        elif stage == "GENERATING":
            console.print(f"[bold cyan]>> Round {data['iteration'] + 1}: Generating Lesson Draft...[/bold cyan]")
        elif stage == "REGENERATING":
            console.print(f"[bold magenta]>> Round {data['iteration'] + 1}: Regenerating with Evaluator Feedback...[/bold magenta]")
        elif stage == "EVALUATING":
            console.print(f"[yellow]Rubric Evaluator: Auditing draft against 6 hard pass/fail checkpoints...[/yellow]")
        elif stage == "MEMORY_EVOLVED":
            console.print(f"[magenta]Self-Evolution: New guardrail rule synthesized into institutional memory.[/magenta]")

    final_state = workflow.run(
        topic=args.topic,
        flaw_injection=args.inject_flaw,
        progress_callback=cli_progress
    )

    console.print("\n" + "=" * 80 + "\n")
    if final_state.evaluation_result:
        display_rubric_card(final_state.evaluation_result, final_state.iteration)
        console.print()

    display_rejection_history(final_state.rejection_history)
    console.print()

    # Evolution report
    evo = memory.get_evolution_report()
    console.print(Panel(
        f"[bold cyan]Institutional Memory Evolution Stats:[/bold cyan]\n"
        f"- Total Runs Executed: {evo['total_runs']}\n"
        f"- Total Rejections Caught & Corrected: {evo['total_rejections_caught_and_corrected']}\n"
        f"- Active Guardrail Directives in Memory: {evo['active_guardrail_rules']}",
        border_style="cyan",
        safe_box=True
    ))

    # Save deliverables
    os.makedirs(args.output_dir, exist_ok=True)
    lesson_path = os.path.join(args.output_dir, "FINAL_LESSON_RAG.md")
    rejection_path = os.path.join(args.output_dir, "REJECTION_LOG.md")

    if final_state.current_draft:
        with open(lesson_path, "w", encoding="utf-8") as f:
            f.write(final_state.current_draft.full_markdown)
        console.print(f"[bold green]Final Lesson Document saved to:[/bold green] {lesson_path}")

    # Write Rejection Log
    with open(rejection_path, "w", encoding="utf-8") as f:
        f.write("# Rejection and Quality Audit Log\n\n")
        f.write(f"**Topic:** {final_state.topic}\n")
        f.write(f"**Final Status:** {final_state.status}\n")
        f.write(f"**Total Retries:** {len(final_state.rejection_history)}\n\n")
        if not final_state.rejection_history:
            f.write("No rejections occurred. Draft cleared all 6 checkpoints on first generation.\n")
        else:
            for r in final_state.rejection_history:
                f.write(f"## Rejection Round {r.iteration + 1}\n\n")
                f.write(f"- **Timestamp:** {r.timestamp}\n")
                f.write(f"- **Failed Checkpoints:** {', '.join(r.failed_checkpoints)}\n")
                f.write(f"- **Root Cause Analysis:**\n```\n{r.root_cause_analysis}\n```\n")
                f.write(f"- **Feedback Injected to Regeneration Prompt:**\n```\n{r.feedback_injected_to_prompt}\n```\n")
                f.write(f"- **Remedy Applied:**\n```\n{r.remedy_applied}\n```\n\n---\n")

    console.print(f"[bold green]Rejection Audit Log saved to:[/bold green] {rejection_path}")

    if args.preview and final_state.current_draft:
        console.print("\n" + "=" * 80 + "\n")
        console.print(Markdown(final_state.current_draft.full_markdown))


if __name__ == "__main__":
    main()
