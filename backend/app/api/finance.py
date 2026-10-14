from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
import datetime
import json
from backend.app.db.session import get_db
from backend.app.models import InvoiceRecord, TaskEvent
from backend.app.schemas import InvoiceCreate, InvoiceUpdate, InvoiceResponse

router = APIRouter(prefix="/finance", tags=["Finance System"])

@router.get("/invoices", response_model=List[InvoiceResponse])
def list_invoices(
    vendor: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(InvoiceRecord)
    if vendor:
        query = query.filter(InvoiceRecord.vendor.ilike(f"%{vendor}%"))
    if status:
        query = query.filter(InvoiceRecord.status == status)
    return query.order_by(InvoiceRecord.created_at.desc()).all()

@router.get("/invoices/{invoice_id}", response_model=InvoiceResponse)
def get_invoice(invoice_id: str, db: Session = Depends(get_db)):
    inv = db.query(InvoiceRecord).filter(
        (InvoiceRecord.id == invoice_id) | (InvoiceRecord.invoice_number == invoice_id)
    ).first()
    if not inv:
        raise HTTPException(status_code=404, detail=f"Invoice '{invoice_id}' not found in finance system.")
    return inv

@router.post("/invoices", response_model=InvoiceResponse, status_code=201)
def create_invoice(payload: InvoiceCreate, db: Session = Depends(get_db)):
    # 1. Enforce Uniqueness & Prevent Duplicates
    existing = db.query(InvoiceRecord).filter(
        InvoiceRecord.invoice_number == payload.invoice_number
    ).first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Duplicate invoice detected: Invoice '{payload.invoice_number}' already exists in finance system (ID: {existing.id})."
        )
    
    # 2. Persist record
    new_inv = InvoiceRecord(
        id=f"rec_{uuid.uuid4().hex[:10]}",
        vendor=payload.vendor,
        invoice_number=payload.invoice_number,
        invoice_date=payload.invoice_date,
        due_date=payload.due_date,
        currency=payload.currency or "USD",
        subtotal=payload.subtotal or 0.0,
        tax=payload.tax or 0.0,
        total_amount=payload.total_amount,
        source_document_id=payload.source_document_id,
        status="RECORDED",
        created_at=datetime.datetime.utcnow(),
        updated_at=datetime.datetime.utcnow()
    )
    db.add(new_inv)
    db.commit()
    db.refresh(new_inv)
    return new_inv

@router.patch("/invoices/{invoice_id}", response_model=InvoiceResponse)
def update_invoice(invoice_id: str, payload: InvoiceUpdate, db: Session = Depends(get_db)):
    inv = db.query(InvoiceRecord).filter(
        (InvoiceRecord.id == invoice_id) | (InvoiceRecord.invoice_number == invoice_id)
    ).first()
    if not inv:
        raise HTTPException(status_code=404, detail=f"Invoice '{invoice_id}' not found.")
    
    update_data = payload.dict(exclude_unset=True)
    for k, v in update_data.items():
        setattr(inv, k, v)
    inv.updated_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(inv)
    return inv

@router.get("/invoices/{invoice_id}/verify")
def verify_invoice_record(invoice_id: str, db: Session = Depends(get_db)):
    """Independent read-back verification of an invoice record."""
    inv = db.query(InvoiceRecord).filter(
        (InvoiceRecord.id == invoice_id) | (InvoiceRecord.invoice_number == invoice_id)
    ).first()
    if not inv:
        return {"exists": False, "verified": False, "detail": "Record not found"}
    return {
        "exists": True,
        "verified": True,
        "record": {
            "id": inv.id,
            "vendor": inv.vendor,
            "invoice_number": inv.invoice_number,
            "invoice_date": inv.invoice_date,
            "due_date": inv.due_date,
            "currency": inv.currency,
            "total_amount": inv.total_amount,
            "status": inv.status
        }
    }

@router.get("/audit")
def get_finance_audit_history(db: Session = Depends(get_db)):
    records = db.query(InvoiceRecord).order_by(InvoiceRecord.updated_at.desc()).all()
    return [{
        "record_id": r.id,
        "invoice_number": r.invoice_number,
        "vendor": r.vendor,
        "total_amount": r.total_amount,
        "status": r.status,
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "updated_at": r.updated_at.isoformat() if r.updated_at else None
    } for r in records]
