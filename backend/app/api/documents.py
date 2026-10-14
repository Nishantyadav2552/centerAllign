from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
from pathlib import Path
import fitz  # PyMuPDF
from backend.app.core.config import INVOICES_DIR

router = APIRouter(prefix="/documents", tags=["Document Management & Extraction"])

@router.get("")
@router.get("/")
def list_documents():
    """Lists synthetic documents in the secure demo repository."""
    docs = []
    if INVOICES_DIR.exists():
        for p in INVOICES_DIR.glob("*.pdf"):
            docs.append({
                "id": p.name,
                "filename": p.name,
                "size_bytes": p.stat().st_size,
                "doc_type": "pdf"
            })
    return docs

@router.get("/{document_id}")
def get_document_details(document_id: str):
    safe_name = Path(document_id).name
    filepath = INVOICES_DIR / safe_name
    if not filepath.exists():
        raise HTTPException(status_code=404, detail=f"Document '{safe_name}' not found.")
    
    doc = fitz.open(str(filepath))
    page_count = len(doc)
    doc.close()
    return {
        "id": safe_name,
        "filename": safe_name,
        "page_count": page_count,
        "size_bytes": filepath.stat().st_size
    }

@router.get("/{document_id}/evidence")
def get_document_evidence(document_id: str):
    """Extracts raw text, blocks, and evidence metadata with page references."""
    safe_name = Path(document_id).name
    filepath = INVOICES_DIR / safe_name
    if not filepath.exists():
        raise HTTPException(status_code=404, detail=f"Document '{safe_name}' not found.")

    doc = fitz.open(str(filepath))
    pages_data = []
    full_text = ""
    for page_idx, page in enumerate(doc):
        text = page.get_text()
        full_text += text + "\n"
        blocks = page.get_text("blocks")
        pages_data.append({
            "page_number": page_idx + 1,
            "text": text,
            "blocks_count": len(blocks)
        })
    doc.close()

    return {
        "document_id": safe_name,
        "pages": pages_data,
        "full_text": full_text
    }
