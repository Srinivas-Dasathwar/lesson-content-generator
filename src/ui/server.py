"""
FastAPI Server for the Interactive Web Interface of the Self-Evaluating Lesson Generator.
Runs on localhost:8000. Provides real-time workflow execution, rubric visualization,
deliberate flaw injection testing, and lesson export.
"""

import os
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

from src.workflow import LessonGeneratorWorkflow
from src.providers.llm_provider import get_llm_provider
from src.memory.institutional_memory import InstitutionalMemory
from src.models import TargetAudience

app = FastAPI(title="Curriculum Studio - Lesson Quality Evaluator", version="1.0.0")

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(STATIC_DIR, exist_ok=True)

class RunWorkflowRequest(BaseModel):
    topic: str = "RAG (Retrieval-Augmented Generation)"
    flaw_injection: str = "none" # "none" | "jargon_bomb" | "hallucinated_facts" | "missing_analogy"
    provider: str = "auto"
    max_retries: int = 2

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        with open(index_file, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse("<h1>Web UI is loading...</h1>")

@app.post("/api/run")
async def run_workflow_api(req: RunWorkflowRequest):
    try:
        llm = get_llm_provider(provider_name=req.provider, flaw_type=req.flaw_injection)
        memory = InstitutionalMemory()
        workflow = LessonGeneratorWorkflow(
            llm_provider=llm,
            memory=memory,
            max_retries=req.max_retries
        )

        final_state = workflow.run(
            topic=req.topic,
            flaw_injection=req.flaw_injection
        )

        return {
            "status": final_state.status,
            "topic": final_state.topic,
            "iteration": final_state.iteration,
            "flaw_injection": final_state.flaw_injection,
            "evaluation_result": final_state.evaluation_result.model_dump() if final_state.evaluation_result else None,
            "rejection_history": [r.model_dump() for r in final_state.rejection_history],
            "current_draft": final_state.current_draft.model_dump() if final_state.current_draft else None,
            "accumulated_memory_rules": final_state.accumulated_memory_rules,
            "execution_logs": final_state.execution_logs,
            "memory_evolution": memory.get_evolution_report()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/memory")
async def get_memory_api():
    memory = InstitutionalMemory()
    return memory.get_evolution_report()

@app.post("/api/reset-memory")
async def reset_memory_api():
    memory = InstitutionalMemory()
    memory._seed_default_rules()
    return {"message": "Memory reset to initial seed guardrails."}

@app.get("/api/download-lesson")
async def download_lesson():
    lesson_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "docs",
        "FINAL_LESSON_RAG.md"
    )
    if os.path.exists(lesson_path):
        with open(lesson_path, "r", encoding="utf-8") as f:
            content = f.read()
        return PlainTextResponse(
            content,
            media_type="text/markdown",
            headers={"Content-Disposition": "attachment; filename=FINAL_LESSON_RAG.md"}
        )
    raise HTTPException(status_code=404, detail="Lesson document not found.")

def start_server(host: str = "127.0.0.1", port: int = 8000):
    print(f"Starting Web UI Dashboard on http://{host}:{port} ...")
    uvicorn.run("src.ui.server:app", host=host, port=port, reload=False)

if __name__ == "__main__":
    start_server()
