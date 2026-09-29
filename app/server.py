"""
FastAPI Server for the Academic Research Papers Generator Agent.
Provides RESTful APIs for paper synthesis, multi-turn AI chat refinement, section editing,
and multi-format academic exports (LaTeX, Word DOCX, PDF).
"""

import os
import sys
import datetime
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.models import (
    PaperDocument, GenerationRequest, ChatRequest,
    SectionUpdateRequest, Author
)
from app.generator.agent import PAPER_AGENT, get_paper, save_paper
from app.generator.templates import TEMPLATES_METADATA
from app.exporters.latex_exporter import export_latex_bundle, generate_latex_source, generate_bibtex
from app.exporters.docx_exporter import export_paper_to_docx
from app.exporters.pdf_exporter import export_paper_to_pdf

app = FastAPI(
    title="Academic Research Paper Generator Agent API",
    description="Full-lifecycle academic paper synthesis, conversational refinement, and multi-format publishing suite.",
    version="1.0.0"
)

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Outputs directory for cached documents & figures
OUTPUTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "outputs"))
STATIC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "static"))
os.makedirs(OUTPUTS_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

# Mount outputs for direct static figure access
app.mount("/outputs", StaticFiles(directory=OUTPUTS_DIR), name="outputs")

# Mount static web assets
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        with open(index_file, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>PaperGen Academic Agent</h1><p>Frontend assets are loading...</p>"

@app.get("/api/health")
async def health_check():
    return {
        "status": "online",
        "system": sys.platform,
        "python_version": sys.version,
        "capabilities": {
            "latex_export": True,
            "bibtex_export": True,
            "docx_export": True,
            "pdf_export": True,
            "chart_generation": True,
            "llm_providers": ["built-in", "openai", "gemini", "ollama"]
        }
    }

@app.get("/api/templates")
async def list_templates():
    return list(TEMPLATES_METADATA.values())

@app.get("/api/presets")
async def list_presets():
    """Curated academic research topics across leading scientific frontiers."""
    return [
        {
            "title": "Quantum-Resistant Cryptographic Routing in Next-Generation 6G Networks",
            "domain": "Cybersecurity & Networks",
            "target_pages": 12,
            "target_references": 36,
            "template": "ieee",
            "description": "Explores lattice-based key exchange protocols and zero-trust mesh routing under post-quantum threat models."
        },
        {
            "title": "Hierarchical State-Space Attention Models for Long-Context Genomic Sequence Modeling",
            "domain": "Biomedical & Healthcare",
            "target_pages": 14,
            "target_references": 42,
            "template": "nature",
            "description": "Combines selective state-space memory with multi-scale attention for zero-shot protein folding and mutation prediction."
        },
        {
            "title": "Decentralized Multi-Agent Reinforcement Learning for Resilient Smart Grid Load Balancing",
            "domain": "Computer Science & AI",
            "target_pages": 12,
            "target_references": 36,
            "template": "ieee",
            "description": "Formulates closed-loop Lyapunov stability bounds for distributed energy storage arbitrage across heterogeneous microgrids."
        },
        {
            "title": "Physics-Informed Neural Differential Equations for Predictive Autonomous Vehicle Dynamics",
            "domain": "Robotics & Control",
            "target_pages": 10,
            "target_references": 30,
            "template": "acm",
            "description": "Integrates Hamiltonian mechanics priors into continuous neural ODE solvers for real-time trajectory optimization."
        },
        {
            "title": "Scalable Geometric Graph Transformers for Molecular Representation and Drug Repurposing",
            "domain": "Computer Science & AI",
            "target_pages": 12,
            "target_references": 38,
            "template": "neurips",
            "description": "Investigates SO(3)-equivariant message-passing networks with provable sub-quadratic memory complexity."
        }
    ]

@app.post("/api/generate", response_model=PaperDocument)
async def generate_paper(req: GenerationRequest):
    """Generates an academic paper conforming to user specifications."""
    try:
        paper = PAPER_AGENT.generate_new_paper(req, output_dir=OUTPUTS_DIR)
        return paper
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

@app.get("/api/paper/{paper_id}", response_model=PaperDocument)
async def get_paper_by_id(paper_id: str):
    paper = get_paper(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    return paper

@app.post("/api/chat")
async def chat_with_paper_agent(req: ChatRequest):
    """Interactive peer-reviewer conversation with the Academic Agent."""
    paper = get_paper(req.paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
        
    reply, proposed_changes = PAPER_AGENT.chat_with_agent(req)
    return {
        "reply": reply,
        "proposed_changes": proposed_changes
    }

@app.post("/api/paper/{paper_id}/apply-change", response_model=PaperDocument)
async def apply_change(paper_id: str, payload: Dict[str, Any]):
    """Applies an agent-proposed change directly into the live paper."""
    change = payload.get("change")
    if not change:
        raise HTTPException(status_code=400, detail="Missing change payload")
    try:
        updated_paper = PAPER_AGENT.apply_change_to_paper(paper_id, change)
        return updated_paper
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/paper/{paper_id}/section/{section_id}", response_model=PaperDocument)
async def update_section(paper_id: str, section_id: str, req: SectionUpdateRequest):
    """Directly updates a specific section's content or title."""
    paper = get_paper(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
        
    found = False
    for s in paper.sections:
        if s.id == section_id:
            if req.title:
                s.title = req.title
            if req.content is not None:
                s.content = req.content
            if req.subsections is not None:
                s.subsections = req.subsections
            found = True
            break
            
    if not found and section_id == "abstract" and req.content:
        paper.abstract = req.content
        found = True

    if not found:
        raise HTTPException(status_code=404, detail="Section not found")

    paper.updated_at = datetime.datetime.now().isoformat()
    save_paper(paper, OUTPUTS_DIR)
    return paper

# ----------------------------------------------------
# EXPORT ENDPOINTS
# ----------------------------------------------------

@app.get("/api/export/{paper_id}/latex")
async def export_latex(paper_id: str):
    paper = get_paper(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
        
    tex_path, _ = export_latex_bundle(paper, OUTPUTS_DIR)
    clean_filename = f"{paper.title[:30].strip().replace(' ', '_')}.tex"
    return FileResponse(
        path=tex_path,
        filename=clean_filename,
        media_type="text/x-tex"
    )

@app.get("/api/export/{paper_id}/latex-zip")
async def export_latex_zip(paper_id: str):
    paper = get_paper(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
        
    _, zip_path = export_latex_bundle(paper, OUTPUTS_DIR)
    clean_filename = f"{paper.title[:30].strip().replace(' ', '_')}_latex_bundle.zip"
    return FileResponse(
        path=zip_path,
        filename=clean_filename,
        media_type="application/zip"
    )

@app.get("/api/export/{paper_id}/bib")
async def export_bib(paper_id: str):
    paper = get_paper(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
        
    bib_content = generate_bibtex(paper)
    bib_path = os.path.join(OUTPUTS_DIR, f"{paper.id}_references.bib")
    with open(bib_path, "w", encoding="utf-8") as f:
        f.write(bib_content)
        
    return FileResponse(
        path=bib_path,
        filename="references.bib",
        media_type="text/plain"
    )

@app.get("/api/export/{paper_id}/docx")
async def export_docx(paper_id: str):
    paper = get_paper(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
        
    doc_path = export_paper_to_docx(paper, OUTPUTS_DIR)
    clean_filename = f"{paper.title[:30].strip().replace(' ', '_')}.docx"
    return FileResponse(
        path=doc_path,
        filename=clean_filename,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

@app.get("/api/export/{paper_id}/pdf")
async def export_pdf(paper_id: str):
    paper = get_paper(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
        
    pdf_path = export_paper_to_pdf(paper, OUTPUTS_DIR)
    clean_filename = f"{paper.title[:30].strip().replace(' ', '_')}.pdf"
    return FileResponse(
        path=pdf_path,
        filename=clean_filename,
        media_type="application/pdf"
    )
