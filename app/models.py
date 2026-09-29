"""
Data models and schemas for the Academic Research Paper Generator Agent.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class Author(BaseModel):
    name: str
    affiliation: str
    email: str
    orcid: Optional[str] = None
    is_corresponding: bool = False

class TableColumn(BaseModel):
    header: str
    align: str = "left"  # left, center, right

class TableData(BaseModel):
    id: str
    caption: str
    headers: List[str]
    rows: List[List[str]]
    note: Optional[str] = None

class FigureData(BaseModel):
    id: str
    caption: str
    file_path: Optional[str] = None
    base64_data: Optional[str] = None
    figure_type: str = "benchmark"  # benchmark, ablation, convergence, architecture

class ReferenceItem(BaseModel):
    index: int
    key: str
    authors: str
    title: str
    venue: str
    year: int
    volume: Optional[str] = None
    pages: Optional[str] = None
    doi: Optional[str] = None
    url: Optional[str] = None
    raw_citation: str

class Subsection(BaseModel):
    id: str
    number: str
    title: str
    content: str

class Section(BaseModel):
    id: str
    number: str
    title: str
    content: str
    subsections: List[Subsection] = []
    tables: List[TableData] = []
    figures: List[FigureData] = []
    algorithms: List[str] = []

class PaperDocument(BaseModel):
    id: str
    title: str
    running_title: Optional[str] = None
    authors: List[Author]
    abstract: str
    keywords: List[str]
    template: str = "ieee"  # ieee, acm, springer, apa, nature, neurips
    domain: str = "Computer Science & AI"
    target_pages: int = 12
    target_references: int = 36
    sections: List[Section] = []
    references: List[ReferenceItem] = []
    figures: List[FigureData] = []
    tables: List[TableData] = []
    created_at: str
    updated_at: str
    stats: Dict[str, Any] = {}

class GenerationRequest(BaseModel):
    model_config = {"protected_namespaces": ()}
    topic: str
    domain: Optional[str] = "Computer Science & AI"
    target_pages: int = Field(default=12, ge=2, le=30)
    target_references: int = Field(default=36, ge=5, le=100)
    template: Optional[str] = "ieee"  # ieee, acm, springer, apa, nature, neurips
    custom_instructions: Optional[str] = ""
    authors: Optional[List[Author]] = None
    include_figures: bool = True
    include_algorithms: bool = True
    include_tables: bool = True
    api_key: Optional[str] = None
    llm_provider: Optional[str] = "built-in"  # built-in, openai, gemini, ollama
    model_name: Optional[str] = None

class ChatMessage(BaseModel):
    role: str  # user, assistant, system
    content: str
    timestamp: Optional[str] = None
    proposed_changes: Optional[Dict[str, Any]] = None  # section_id, new_content, diff

class ChatRequest(BaseModel):
    model_config = {"protected_namespaces": ()}
    paper_id: str
    message: str
    selected_section_id: Optional[str] = None
    history: List[ChatMessage] = []
    api_key: Optional[str] = None
    llm_provider: Optional[str] = "built-in"
    model_name: Optional[str] = None

class SectionUpdateRequest(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    subsections: Optional[List[Subsection]] = None

class ExportResponse(BaseModel):
    download_url: str
    filename: str
    format: str
    size_bytes: int
