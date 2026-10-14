from typing import Dict, Any, List, Optional
import uuid
import datetime
from backend.app.tools.registry import tool_registry
from backend.app.models import InvoiceRecord
from backend.app.core.config import settings

@tool_registry.register(
    name="finance_search_invoices",
    description="Search internal finance system for existing invoices by invoice number or vendor.",
    input_schema={
        "type": "object",
        "properties": {
            "invoice_number": {"type": "string", "description": "Specific invoice number to query"},
            "vendor": {"type": "string", "description": "Vendor name keyword"}
        }
    },
    permission="read"
)
def finance_search_invoices(context: Dict[str, Any], invoice_number: Optional[str] = None, vendor: Optional[str] = None) -> Dict[str, Any]:
    db = context["db_session"]
    query = db.query(InvoiceRecord)
    if invoice_number:
        query = query.filter(InvoiceRecord.invoice_number == invoice_number)
    if vendor:
        query = query.filter(InvoiceRecord.vendor.ilike(f"%{vendor}%"))
    
    matches = query.all()
    results = [
        {
            "id": inv.id,
            "invoice_number": inv.invoice_number,
            "vendor": inv.vendor,
            "invoice_date": inv.invoice_date,
            "due_date": inv.due_date,
            "total_amount": inv.total_amount,
            "currency": inv.currency,
            "status": inv.status
        }
        for inv in matches
    ]
    return {
        "found": len(results) > 0,
        "count": len(results),
        "invoices": results
    }

@tool_registry.register(
    name="finance_get_invoice",
    description="Retrieve a single invoice record by ID or invoice number from the finance database.",
    input_schema={
        "type": "object",
        "properties": {
            "invoice_identifier": {"type": "string", "description": "Database ID or invoice number"}
        },
        "required": ["invoice_identifier"]
    },
    permission="read"
)
def finance_get_invoice(context: Dict[str, Any], invoice_identifier: str) -> Dict[str, Any]:
    db = context["db_session"]
    inv = db.query(InvoiceRecord).filter(
        (InvoiceRecord.id == invoice_identifier) | (InvoiceRecord.invoice_number == invoice_identifier)
    ).first()
    if not inv:
        return {"found": False, "error": f"Invoice '{invoice_identifier}' not found in finance system."}
    
    return {
        "found": True,
        "invoice": {
            "id": inv.id,
            "invoice_number": inv.invoice_number,
            "vendor": inv.vendor,
            "invoice_date": inv.invoice_date,
            "due_date": inv.due_date,
            "total_amount": inv.total_amount,
            "currency": inv.currency,
            "status": inv.status,
            "created_at": inv.created_at.isoformat() if inv.created_at else None
        }
    }

@tool_registry.register(
    name="finance_create_invoice",
    description="Create a new invoice record in the internal finance system. Enforces uniqueness rules and idempotency.",
    input_schema={
        "type": "object",
        "properties": {
            "vendor": {"type": "string"},
            "invoice_number": {"type": "string"},
            "invoice_date": {"type": "string"},
            "due_date": {"type": "string"},
            "total_amount": {"type": "number"},
            "currency": {"type": "string", "default": "USD"},
            "subtotal": {"type": "number", "default": 0.0},
            "tax": {"type": "number", "default": 0.0},
            "source_document_id": {"type": "string"}
        },
        "required": ["vendor", "invoice_number", "invoice_date", "due_date", "total_amount"]
    },
    requires_approval=True,  # Consequential financial action!
    permission="sensitive_write"
)
def finance_create_invoice(
    context: Dict[str, Any],
    vendor: str,
    invoice_number: str,
    invoice_date: str,
    due_date: str,
    total_amount: float,
    currency: str = "USD",
    subtotal: float = 0.0,
    tax: float = 0.0,
    source_document_id: Optional[str] = None
) -> Dict[str, Any]:
    db = context["db_session"]

    # 1. Uniqueness / Duplicate check
    existing = db.query(InvoiceRecord).filter(InvoiceRecord.invoice_number == invoice_number).first()
    if existing:
        return {
            "success": False,
            "duplicate": True,
            "error": f"Invoice '{invoice_number}' already exists in finance system (Record ID: {existing.id}). Creation blocked to prevent duplicate.",
            "existing_record_id": existing.id
        }

    # 2. Persist in database
    rec_id = f"inv_{uuid.uuid4().hex[:8]}"
    record = InvoiceRecord(
        id=rec_id,
        vendor=vendor,
        invoice_number=invoice_number,
        invoice_date=invoice_date,
        due_date=due_date,
        currency=currency,
        subtotal=subtotal,
        tax=tax,
        total_amount=total_amount,
        source_document_id=source_document_id,
        status="RECORDED",
        created_at=datetime.datetime.utcnow(),
        updated_at=datetime.datetime.utcnow()
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return {
        "success": True,
        "record_id": record.id,
        "invoice_number": record.invoice_number,
        "vendor": record.vendor,
        "total_amount": record.total_amount,
        "status": record.status,
        "message": f"Successfully created invoice record '{invoice_number}' with ID '{record.id}'."
    }

@tool_registry.register(
    name="finance_update_invoice",
    description="Update an existing invoice record in the finance system.",
    input_schema={
        "type": "object",
        "properties": {
            "invoice_identifier": {"type": "string"},
            "updates": {"type": "object"}
        },
        "required": ["invoice_identifier", "updates"]
    },
    requires_approval=True,
    permission="sensitive_write"
)
def finance_update_invoice(context: Dict[str, Any], invoice_identifier: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    db = context["db_session"]
    inv = db.query(InvoiceRecord).filter(
        (InvoiceRecord.id == invoice_identifier) | (InvoiceRecord.invoice_number == invoice_identifier)
    ).first()
    if not inv:
        return {"success": False, "error": f"Invoice '{invoice_identifier}' not found."}

    for k, v in updates.items():
        if hasattr(inv, k):
            setattr(inv, k, v)
    inv.updated_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(inv)

    return {"success": True, "record_id": inv.id, "message": f"Invoice '{inv.invoice_number}' updated."}

@tool_registry.register(
    name="finance_verify_invoice",
    description="Perform an independent read-back and field-by-field verification of a saved invoice in SQLite against expected source fields.",
    input_schema={
        "type": "object",
        "properties": {
            "invoice_number": {"type": "string"},
            "expected_fields": {"type": "object"}
        },
        "required": ["invoice_number", "expected_fields"]
    },
    permission="read"
)
def finance_verify_invoice(context: Dict[str, Any], invoice_number: str, expected_fields: Dict[str, Any]) -> Dict[str, Any]:
    db = context["db_session"]
    inv = db.query(InvoiceRecord).filter(InvoiceRecord.invoice_number == invoice_number).first()
    if not inv:
        return {
            "verified": False,
            "error": f"Independent read-back verification failed: Invoice '{invoice_number}' does not exist in SQLite database.",
            "field_matches": {}
        }

    field_matches = {}
    all_matched = True

    checks = {
        "invoice_number": inv.invoice_number,
        "vendor": inv.vendor,
        "invoice_date": inv.invoice_date,
        "due_date": inv.due_date,
        "total_amount": inv.total_amount
    }

    for field, actual_val in checks.items():
        if field in expected_fields:
            exp_val = expected_fields[field]
            if isinstance(actual_val, float) or isinstance(exp_val, (int, float)):
                match = abs(float(actual_val) - float(exp_val)) < 0.01
            else:
                match = str(actual_val).strip() == str(exp_val).strip()
            field_matches[field] = {
                "expected": exp_val,
                "actual": actual_val,
                "match": match
            }
            if not match:
                all_matched = False

    return {
        "verified": all_matched,
        "record_id": inv.id,
        "field_matches": field_matches,
        "summary": "All fields verified identically against SQLite persistence." if all_matched else "Field discrepancies detected during verification."
    }

@tool_registry.register(
    name="finance_get_audit_history",
    description="Retrieve finance system ledger audit history.",
    input_schema={"type": "object", "properties": {}},
    permission="read"
)
def finance_get_audit_history(context: Dict[str, Any]) -> Dict[str, Any]:
    db = context["db_session"]
    records = db.query(InvoiceRecord).order_by(InvoiceRecord.updated_at.desc()).all()
    return {
        "total_records": len(records),
        "audit_trail": [
            {
                "id": r.id,
                "invoice_number": r.invoice_number,
                "vendor": r.vendor,
                "total_amount": r.total_amount,
                "status": r.status,
                "updated_at": r.updated_at.isoformat() if r.updated_at else None
            }
            for r in records
        ]
    }
