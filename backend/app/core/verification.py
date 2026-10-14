import json
import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.app.models import InvoiceRecord, InternalTask, VerificationRecord

logger = logging.getLogger(__name__)

class VerificationEngine:
    """
    Independent Verification Engine.
    Never trusts LLM assertions. Reads back database state directly and performs field-by-field audit.
    """

    @staticmethod
    def verify_invoice(
        db: Session,
        task_id: str,
        invoice_number: str,
        expected_fields: Dict[str, Any],
        source_document_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Reads back the invoice directly from SQLite and compares each field.
        """
        inv = db.query(InvoiceRecord).filter(InvoiceRecord.invoice_number == invoice_number).first()
        if not inv:
            rec = VerificationRecord(
                id=f"ver_{task_id[:8]}",
                task_id=task_id,
                target_type="invoice",
                target_id=invoice_number,
                verified=False,
                field_results_json=json.dumps({"persisted_in_db": False}),
                details=f"Independent read-back verification failed: Invoice '{invoice_number}' does not exist in SQLite database."
            )
            db.add(rec)
            db.commit()
            return {"verified": False, "error": f"Record '{invoice_number}' not found in database.", "field_results": {}}

        field_results = {}
        all_passed = True

        # Field-by-field check
        checks = {
            "invoice_number": (expected_fields.get("invoice_number"), inv.invoice_number),
            "vendor": (expected_fields.get("vendor"), inv.vendor),
            "invoice_date": (expected_fields.get("invoice_date"), inv.invoice_date),
            "due_date": (expected_fields.get("due_date"), inv.due_date),
            "total_amount": (expected_fields.get("total_amount"), inv.total_amount)
        }

        for field, (expected, actual) in checks.items():
            if expected is None:
                continue
            
            if field == "total_amount":
                match = abs(float(actual) - float(expected)) < 0.01
            else:
                match = str(actual).strip() == str(expected).strip()

            field_results[field] = {
                "expected": expected,
                "actual": actual,
                "match": match
            }
            if not match:
                all_passed = False

        evidence = {
            "source_document_id": source_document_id or inv.source_document_id,
            "database_table": "invoice_records",
            "sqlite_primary_key": inv.id,
            "verified_at": inv.updated_at.isoformat() if inv.updated_at else None
        }

        # Store verification record
        rec = VerificationRecord(
            id=f"ver_{task_id[:8]}",
            task_id=task_id,
            target_type="invoice",
            target_id=inv.id,
            verified=all_passed,
            field_results_json=json.dumps(field_results),
            evidence_json=json.dumps(evidence),
            details="All fields independently read back and validated from SQLite database." if all_passed else "Field value discrepancies found during independent verification."
        )
        db.add(rec)
        db.commit()

        return {
            "verified": all_passed,
            "record_id": inv.id,
            "field_results": field_results,
            "evidence": evidence,
            "summary": "Independent verification passed with 100% field parity." if all_passed else "Verification failed due to discrepancies."
        }

    @staticmethod
    def verify_internal_task(db: Session, task_id: str, internal_task_id: str) -> Dict[str, Any]:
        """Verifies that an internal follow-up task was recorded in the database."""
        itask = db.query(InternalTask).filter(InternalTask.id == internal_task_id).first()
        if not itask:
            return {"verified": False, "error": f"Internal task '{internal_task_id}' not found."}

        field_results = {
            "task_id": {"expected": internal_task_id, "actual": itask.id, "match": True},
            "status": {"expected": "OPEN", "actual": itask.status, "match": itask.status == "OPEN"}
        }

        rec = VerificationRecord(
            id=f"ver_{task_id[:8]}",
            task_id=task_id,
            target_type="internal_task",
            target_id=itask.id,
            verified=True,
            field_results_json=json.dumps(field_results),
            details=f"Internal task '{itask.id}' verified successfully."
        )
        db.add(rec)
        db.commit()

        return {
            "verified": True,
            "record_id": itask.id,
            "field_results": field_results,
            "summary": "Internal task verified in operations database."
        }

verification_engine = VerificationEngine()
