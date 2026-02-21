"""
FastAPI application for RAG IT Infrastructure Assistant.
"""

import os
import time
import uuid
from pathlib import Path
from typing import List, Optional, Dict

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from rag_bot.config import (
    CHROMA_DB_DIR, UPLOAD_DIR, ANTHROPIC_API_KEY, ANTHROPIC_MODEL,
    EMBED_MODEL_NAME, COLLECTION_NAME, PROJECT_ROOT
)
from rag_bot.retrieval.retriever import (
    hybrid_retrieve, retrieve_by_vendor, get_collection,
    get_embedder, reload_collection,
)
from rag_bot.generation.generator import (
    generate_answer, generate_comparison, generate_config,
    generate_troubleshoot,
)
from rag_bot.session_manager import session_manager
from rag_bot.ingestion.pdf_loader import extract_pdf_text, chunk_text as chunk_text_pdf
from rag_bot.ingestion.html_loader import extract_html_text, chunk_text as chunk_text_html


# ─── App Setup ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="RAG IT Infrastructure Assistant",
    description="Multi-agent RAG system for IT infrastructure documentation",
    version="2.0.0",
)

# CORS for Angular dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://127.0.0.1:4200", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Request/Response Models ─────────────────────────────────────────────────

class MessageItem(BaseModel):
    role: str  # "user" or "assistant"
    content: str

class QueryRequest(BaseModel):
    question: str
    session_id: Optional[str] = None
    top_k: Optional[int] = 5
    conversation_history: Optional[List[MessageItem]] = None

class SourceInfo(BaseModel):
    vendor: str
    document: str
    page: Optional[str] = "n/a"
    chunk: Optional[int] = None

class QueryResponse(BaseModel):
    answer: str
    sources: List[SourceInfo]
    session_id: str

class CompareRequest(BaseModel):
    vendors: List[str]
    topic: str
    top_k: Optional[int] = 5

class CompareResponse(BaseModel):
    comparison: str
    vendors_found: List[str]
    sources: List[SourceInfo]

class ConfigGenRequest(BaseModel):
    request: str
    vendor: Optional[str] = None
    top_k: Optional[int] = 5

class ConfigGenResponse(BaseModel):
    config: str
    sources: List[SourceInfo]

class TroubleshootRequest(BaseModel):
    problem: str
    session_id: Optional[str] = None
    top_k: Optional[int] = 5
    conversation_history: Optional[List[MessageItem]] = None

class TroubleshootResponse(BaseModel):
    diagnosis: str
    sources: List[SourceInfo]
    session_id: str

class DocumentInfo(BaseModel):
    id: str
    vendor: str
    document: str
    page: Optional[str] = None
    chunk: Optional[int] = None

class DocumentListResponse(BaseModel):
    documents: List[Dict]
    total_chunks: int

class AnalyticsResponse(BaseModel):
    total_queries: int
    active_sessions: int
    avg_response_time: float
    popular_topics: List[Dict]
    recent_queries: List[Dict]
    total_documents: int

class ConfigUpdateRequest(BaseModel):
    anthropic_model: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    version: str
    chromadb_count: int
    model: str
    embedding_model: str


# ─── Helper Functions ────────────────────────────────────────────────────────

def _parse_sources(metadatas: List[Dict]) -> List[SourceInfo]:
    """Convert metadata dicts to SourceInfo list."""
    return [
        SourceInfo(
            vendor=m.get("vendor", "Unknown"),
            document=m.get("document", "Unknown"),
            page=str(m.get("page", "n/a")),
            chunk=m.get("chunk"),
        )
        for m in metadatas
    ]


# ─── Endpoints ───────────────────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse)
def health_check():
    """Health check endpoint."""
    col = get_collection()
    return HealthResponse(
        status="healthy",
        version="2.0.0",
        chromadb_count=col.count(),
        model=ANTHROPIC_MODEL,
        embedding_model=EMBED_MODEL_NAME,
    )


@app.post("/query", response_model=QueryResponse)
def query_rag(request: QueryRequest):
    """Query with hybrid search and multi-turn conversation."""
    t0 = time.time()
    try:
        # Session management
        session_id = request.session_id or session_manager.create_session()

        # Build conversation history
        history = []
        if request.conversation_history:
            history = [{"role": m.role, "content": m.content} for m in request.conversation_history]
        elif request.session_id:
            history = session_manager.get_history(session_id)

        # Hybrid retrieval
        context_chunks, metadatas = hybrid_retrieve(request.question, top_k=request.top_k)

        if not context_chunks:
            answer = "❌ No relevant information found in the indexed documents."
            sources = []
        else:
            answer = generate_answer(
                question=request.question,
                context_chunks=context_chunks,
                metadatas=metadatas,
                conversation_history=history if history else None,
            )
            sources = _parse_sources(metadatas)

        # Track in session
        session_manager.add_message(session_id, "user", request.question)
        session_manager.add_message(session_id, "assistant", answer)

        # Analytics
        response_time = time.time() - t0
        session_manager.track_query(request.question, response_time)

        return QueryResponse(answer=answer, sources=sources, session_id=session_id)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    vendor: str = Form(default="Uploaded"),
):
    """Upload a PDF or HTML file and ingest it into ChromaDB."""
    try:
        filename = file.filename or "unknown"
        ext = Path(filename).suffix.lower()
        if ext not in (".pdf", ".html", ".htm"):
            raise HTTPException(status_code=400, detail="Only PDF and HTML files are supported.")

        # Save uploaded file
        vendor_dir = UPLOAD_DIR / vendor
        vendor_dir.mkdir(parents=True, exist_ok=True)
        file_path = vendor_dir / filename

        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)

        # Ingest into ChromaDB
        col = get_collection()
        emb = get_embedder()
        chunks_added = 0

        if ext == ".pdf":
            pages = extract_pdf_text(file_path)
            for page in pages:
                chunks = chunk_text_pdf(page["text"])
                for idx, chunk in enumerate(chunks):
                    embedding = emb.encode(chunk).tolist()
                    metadata = {
                        "vendor": vendor,
                        "document": filename,
                        "page": page["page_num"],
                        "chunk": idx,
                        "source_path": str(file_path),
                    }
                    doc_id = f"{vendor}_{filename}_p{page['page_num']}_c{idx}"
                    col.add(
                        documents=[chunk],
                        embeddings=[embedding],
                        metadatas=[metadata],
                        ids=[doc_id],
                    )
                    chunks_added += 1
        else:
            text = extract_html_text(file_path)
            chunks = chunk_text_html(text)
            for idx, chunk in enumerate(chunks):
                embedding = emb.encode(chunk).tolist()
                metadata = {
                    "vendor": vendor,
                    "document": filename,
                    "chunk": idx,
                    "source_path": str(file_path),
                }
                doc_id = f"{vendor}_{filename}_c{idx}"
                col.add(
                    documents=[chunk],
                    embeddings=[embedding],
                    metadatas=[metadata],
                    ids=[doc_id],
                )
                chunks_added += 1

        reload_collection()

        return {
            "status": "success",
            "filename": filename,
            "vendor": vendor,
            "chunks_added": chunks_added,
            "total_in_collection": col.count(),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/documents", response_model=DocumentListResponse)
def list_documents():
    """List all indexed documents with counts."""
    col = get_collection()
    all_data = col.get(include=["metadatas"])
    metadatas = all_data.get("metadatas", [])

    # Group by vendor + document
    doc_counts: Dict[str, Dict] = {}
    for meta in metadatas:
        vendor = meta.get("vendor", "Unknown")
        doc_name = meta.get("document", "Unknown")
        key = f"{vendor}/{doc_name}"
        if key not in doc_counts:
            doc_counts[key] = {
                "vendor": vendor,
                "document": doc_name,
                "chunk_count": 0,
                "pages": set(),
            }
        doc_counts[key]["chunk_count"] += 1
        page = meta.get("page")
        if page is not None:
            doc_counts[key]["pages"].add(page)

    # Convert sets to lists for JSON serialization
    documents = []
    for key, info in sorted(doc_counts.items()):
        documents.append({
            "vendor": info["vendor"],
            "document": info["document"],
            "chunk_count": info["chunk_count"],
            "page_count": len(info["pages"]),
        })

    return DocumentListResponse(
        documents=documents,
        total_chunks=len(metadatas),
    )


@app.delete("/documents/{vendor}/{document_name}")
def delete_document(vendor: str, document_name: str):
    """Remove a document from the index."""
    col = get_collection()
    all_data = col.get(include=["metadatas"])
    ids_to_delete = []

    for i, meta in enumerate(all_data.get("metadatas", [])):
        if meta.get("vendor") == vendor and meta.get("document") == document_name:
            ids_to_delete.append(all_data["ids"][i])

    if not ids_to_delete:
        raise HTTPException(status_code=404, detail="Document not found in index.")

    col.delete(ids=ids_to_delete)
    reload_collection()

    return {
        "status": "deleted",
        "vendor": vendor,
        "document": document_name,
        "chunks_removed": len(ids_to_delete),
        "total_remaining": col.count(),
    }


@app.post("/compare", response_model=CompareResponse)
def compare_vendors(request: CompareRequest):
    """Compare multiple vendors or topics."""
    try:
        vendor_contexts: Dict[str, List[str]] = {}
        vendor_metadatas: Dict[str, List[Dict]] = {}
        all_sources = []
        vendors_found = []

        for vendor in request.vendors:
            chunks, metas = retrieve_by_vendor(
                request.topic, vendor, top_k=request.top_k
            )
            if chunks:
                vendor_contexts[vendor] = chunks
                vendor_metadatas[vendor] = metas
                vendors_found.append(vendor)
                all_sources.extend(_parse_sources(metas))

        if not vendors_found:
            # Fall back to general search
            chunks, metas = hybrid_retrieve(
                f"{request.topic} {' '.join(request.vendors)}",
                top_k=request.top_k * len(request.vendors),
            )
            if chunks:
                vendor_contexts["General"] = chunks
                vendor_metadatas["General"] = metas
                vendors_found = request.vendors
                all_sources = _parse_sources(metas)

        comparison = generate_comparison(
            vendors=request.vendors,
            vendor_contexts=vendor_contexts,
            vendor_metadatas=vendor_metadatas,
            topic=request.topic,
        )

        return CompareResponse(
            comparison=comparison,
            vendors_found=vendors_found,
            sources=all_sources,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/config-gen", response_model=ConfigGenResponse)
def generate_configuration(request: ConfigGenRequest):
    """Generate configuration based on documentation."""
    try:
        if request.vendor:
            chunks, metas = retrieve_by_vendor(
                request.request, request.vendor, top_k=request.top_k
            )
        else:
            chunks, metas = hybrid_retrieve(request.request, top_k=request.top_k)

        if not chunks:
            return ConfigGenResponse(
                config="❌ No relevant documentation found to generate configuration.",
                sources=[],
            )

        config = generate_config(
            context_chunks=chunks,
            metadatas=metas,
            config_request=request.request,
        )

        return ConfigGenResponse(
            config=config,
            sources=_parse_sources(metas),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/troubleshoot", response_model=TroubleshootResponse)
def troubleshoot_issue(request: TroubleshootRequest):
    """Multi-step troubleshooting agent."""
    t0 = time.time()
    try:
        session_id = request.session_id or session_manager.create_session()

        # Build conversation history
        history = []
        if request.conversation_history:
            history = [{"role": m.role, "content": m.content} for m in request.conversation_history]
        elif request.session_id:
            history = session_manager.get_history(session_id)

        # Retrieve relevant docs
        chunks, metas = hybrid_retrieve(request.problem, top_k=request.top_k)

        diagnosis = generate_troubleshoot(
            context_chunks=chunks,
            metadatas=metas,
            problem_description=request.problem,
            conversation_history=history if history else None,
        )

        # Track in session
        session_manager.add_message(session_id, "user", request.problem)
        session_manager.add_message(session_id, "assistant", diagnosis)

        response_time = time.time() - t0
        session_manager.track_query(request.problem, response_time)

        return TroubleshootResponse(
            diagnosis=diagnosis,
            sources=_parse_sources(metas) if metas else [],
            session_id=session_id,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analytics", response_model=AnalyticsResponse)
def get_analytics():
    """Get query analytics."""
    analytics = session_manager.get_analytics()
    col = get_collection()
    return AnalyticsResponse(
        total_queries=analytics["total_queries"],
        active_sessions=analytics["active_sessions"],
        avg_response_time=analytics["avg_response_time"],
        popular_topics=analytics["popular_topics"],
        recent_queries=analytics["recent_queries"],
        total_documents=col.count(),
    )


@app.post("/config")
def update_config(request: ConfigUpdateRequest):
    """Update runtime configuration."""
    import rag_bot.config as cfg
    if request.anthropic_model:
        cfg.ANTHROPIC_MODEL = request.anthropic_model
    return {"status": "updated", "model": cfg.ANTHROPIC_MODEL}


@app.get("/config")
def get_config():
    """Get current configuration."""
    return {
        "model": ANTHROPIC_MODEL,
        "embedding_model": EMBED_MODEL_NAME,
        "has_api_key": bool(ANTHROPIC_API_KEY and ANTHROPIC_API_KEY != "your-key-here"),
    }


# ─── Serve Angular static files (production) ────────────────────────────────
# Mount after all API routes

_frontend_dist = PROJECT_ROOT / "frontend" / "rag-bot-ui" / "dist" / "rag-bot-ui"
if _frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(_frontend_dist), html=True), name="frontend")


# ─── Main ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("rag_bot.main:app", host="0.0.0.0", port=8000, reload=True)
