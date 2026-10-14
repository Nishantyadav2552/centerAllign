from typing import Dict, Any, List, Optional
from backend.app.tools.registry import tool_registry
from backend.app.services.document_service import DocumentService
from backend.app.core.config import INVOICES_DIR

@tool_registry.register(
    name="list_documents",
    description="List all available documents in the demo repository.",
    input_schema={"type": "object", "properties": {}},
    permission="read"
)
def list_documents(context: Dict[str, Any]) -> Dict[str, Any]:
    docs = []
    if INVOICES_DIR.exists():
        for p in INVOICES_DIR.glob("*.pdf"):
            docs.append({
                "document_id": p.name,
                "filename": p.name,
                "size_bytes": p.stat().st_size
            })
    return {"documents": docs, "total_count": len(docs)}

@tool_registry.register(
    name="search_documents",
    description="Search documents by filename or vendor keyword.",
    input_schema={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search keyword or filename substring"}
        },
        "required": ["query"]
    },
    permission="read"
)
def search_documents(context: Dict[str, Any], query: str) -> Dict[str, Any]:
    q = query.lower()
    matches = []
    if INVOICES_DIR.exists():
        for p in INVOICES_DIR.glob("*.pdf"):
            if q in p.name.lower():
                matches.append({"document_id": p.name, "filename": p.name})
    return {"query": query, "matches": matches, "match_count": len(matches)}

@tool_registry.register(
    name="extract_pdf_text",
    description="Extract raw full text from a PDF document.",
    input_schema={
        "type": "object",
        "properties": {
            "document_id": {"type": "string", "description": "Filename or identifier of the PDF"}
        },
        "required": ["document_id"]
    },
    permission="read"
)
def extract_pdf_text(context: Dict[str, Any], document_id: str) -> Dict[str, Any]:
    return DocumentService.extract_text(document_id)

@tool_registry.register(
    name="extract_invoice_fields",
    description="Extract structured invoice fields (vendor, invoice_number, date, due_date, amounts, currency) with provenance evidence.",
    input_schema={
        "type": "object",
        "properties": {
            "document_id": {"type": "string", "description": "Filename or identifier of the invoice PDF"}
        },
        "required": ["document_id"]
    },
    permission="read"
)
def extract_invoice_fields(context: Dict[str, Any], document_id: str) -> Dict[str, Any]:
    return DocumentService.extract_invoice_fields(document_id)

@tool_registry.register(
    name="validate_invoice_fields",
    description="Validate extracted invoice values against business rules, required fields, date formats, and arithmetic consistency.",
    input_schema={
        "type": "object",
        "properties": {
            "fields": {"type": "object", "description": "Extracted invoice fields dictionary"}
        },
        "required": ["fields"]
    },
    permission="read"
)
def validate_invoice_fields(context: Dict[str, Any], fields: Dict[str, Any]) -> Dict[str, Any]:
    return DocumentService.validate_fields(fields)

@tool_registry.register(
    name="get_document_evidence",
    description="Retrieve specific evidence excerpts and page provenance for extracted values.",
    input_schema={
        "type": "object",
        "properties": {
            "document_id": {"type": "string", "description": "Document filename or identifier"}
        },
        "required": ["document_id"]
    },
    permission="read"
)
def get_document_evidence(context: Dict[str, Any], document_id: str) -> Dict[str, Any]:
    return DocumentService.extract_invoice_fields(document_id).get("source_evidence", [])
