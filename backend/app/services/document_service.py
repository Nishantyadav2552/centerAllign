import re
from pathlib import Path
from typing import Dict, Any, List, Optional
import fitz  # PyMuPDF
from backend.app.core.config import INVOICES_DIR

class DocumentService:
    """Document Extraction and Structured Field Validation Service."""

    INJECTION_PATTERNS = [
        r"ignore (all )?previous instructions",
        r"system prompt",
        r"you are now an unrestricted",
        r"delete from",
        r"drop table",
        r"<script>",
        r"curl\s+http"
    ]

    @staticmethod
    def extract_text(document_id: str) -> Dict[str, Any]:
        safe_name = Path(document_id).name
        filepath = INVOICES_DIR / safe_name
        if not filepath.exists():
            raise FileNotFoundError(f"Document '{safe_name}' not found.")

        doc = fitz.open(str(filepath))
        pages_content = []
        full_text = ""
        for i, page in enumerate(doc):
            t = page.get_text()
            full_text += t + "\n"
            pages_content.append({"page": i + 1, "text": t})
        doc.close()

        # Security check: prompt injection detection
        injections_found = []
        for pat in DocumentService.INJECTION_PATTERNS:
            if re.search(pat, full_text, re.IGNORECASE):
                injections_found.append(pat)

        return {
            "document_id": safe_name,
            "full_text": full_text,
            "pages": pages_content,
            "injection_detected": len(injections_found) > 0,
            "injection_patterns": injections_found
        }

    @staticmethod
    def extract_invoice_fields(document_id: str) -> Dict[str, Any]:
        """Extracts structured invoice fields and records source evidence."""
        safe_name = Path(document_id).name
        extracted = DocumentService.extract_text(document_id)
        text = extracted["full_text"]
        evidence = []

        # 1. Vendor
        vendor = "Unknown"
        vendor_match = re.search(r"FROM:\s*\n([^\n]+)", text)
        if vendor_match:
            vendor = vendor_match.group(1).strip()
            evidence.append({"field": "vendor", "excerpt": vendor_match.group(0), "page": 1, "method": "header_anchor"})
        elif "Acme Corp" in text:
            vendor = "Acme Corp"
            evidence.append({"field": "vendor", "excerpt": "Acme Corp found in document body", "page": 1, "method": "keyword_match"})
        elif "Globex" in text:
            vendor = "Globex Corp"
            evidence.append({"field": "vendor", "excerpt": "Globex Corp found in document body", "page": 1, "method": "keyword_match"})

        # 2. Invoice Number
        invoice_number = None
        inv_match = re.search(r"Invoice Number:\s*([A-Za-z0-9\-]+)", text) or re.search(r"#([A-Za-z0-9\-]+)", text)
        if inv_match:
            invoice_number = inv_match.group(1).strip()
            evidence.append({"field": "invoice_number", "excerpt": inv_match.group(0), "page": 1, "method": "regex_labeled"})

        # 3. Invoice Date
        invoice_date = None
        date_match = re.search(r"Invoice Date:\s*(\d{4}-\d{2}-\d{2})", text)
        if date_match:
            invoice_date = date_match.group(1).strip()
            evidence.append({"field": "invoice_date", "excerpt": date_match.group(0), "page": 1, "method": "date_regex"})

        # 4. Due Date & Ambiguity Check
        due_date = None
        is_ambiguous = False
        due_match = re.search(r"Due Date:\s*([^\n]+)", text)
        if due_match:
            raw_due = due_match.group(1).strip()
            if "AMBIGUOUS" in raw_due or "PENDING" in raw_due or not re.search(r"\d{4}-\d{2}-\d{2}", raw_due):
                is_ambiguous = True
                due_date = raw_due
            else:
                due_date = re.search(r"\d{4}-\d{2}-\d{2}", raw_due).group(0)
            evidence.append({"field": "due_date", "excerpt": due_match.group(0), "page": 1, "method": "due_date_labeled"})
        else:
            is_ambiguous = True

        # 5. Currency
        currency = "USD"
        curr_match = re.search(r"Currency:\s*([A-Za-z]{3})", text)
        if curr_match:
            currency = curr_match.group(1).strip()
        elif "INR" in text:
            currency = "INR"
        elif "EUR" in text:
            currency = "EUR"

        # 6. Totals & Arithmetic
        subtotal = 0.0
        tax = 0.0
        total_amount = 0.0

        sub_match = re.search(r"Subtotal:\s*[A-Z]{0,3}\s*([\d,]+\.\d{2})", text)
        if sub_match:
            subtotal = float(sub_match.group(1).replace(",", ""))
            evidence.append({"field": "subtotal", "excerpt": sub_match.group(0), "page": 1, "method": "subtotal_regex"})

        tax_match = re.search(r"Tax[^:]*:\s*[A-Z]{0,3}\s*([\d,]+\.\d{2})", text)
        if tax_match:
            tax = float(tax_match.group(1).replace(",", ""))
            evidence.append({"field": "tax", "excerpt": tax_match.group(0), "page": 1, "method": "tax_regex"})

        total_match = re.search(r"Total Amount:\s*[A-Z]{0,3}\s*([\d,]+\.\d{2})", text)
        if total_match:
            total_amount = float(total_match.group(1).replace(",", ""))
            evidence.append({"field": "total_amount", "excerpt": total_match.group(0), "page": 1, "method": "total_regex"})

        return {
            "vendor": vendor,
            "invoice_number": invoice_number,
            "invoice_date": invoice_date,
            "due_date": due_date,
            "is_ambiguous": is_ambiguous,
            "currency": currency,
            "subtotal": subtotal,
            "tax": tax,
            "total_amount": total_amount,
            "source_document_id": safe_name,
            "source_evidence": evidence,
            "prompt_injection_flagged": extracted["injection_detected"]
        }

    @staticmethod
    def validate_fields(fields: Dict[str, Any]) -> Dict[str, Any]:
        """Validates extracted invoice data and returns audit breakdown."""
        errors = []
        warnings = []
        checks = {}

        # 1. Required fields
        for req in ["vendor", "invoice_number", "invoice_date", "total_amount"]:
            val = fields.get(req)
            if not val:
                errors.append(f"Missing required field: '{req}'")
                checks[req] = False
            else:
                checks[req] = True

        # 2. Due date ambiguity
        due_date = fields.get("due_date")
        if not due_date or fields.get("is_ambiguous") or "AMBIGUOUS" in str(due_date) or "PENDING" in str(due_date):
            warnings.append("Ambiguous or unparseable due date detected. Must request human clarification.")
            checks["due_date_valid"] = False
        else:
            checks["due_date_valid"] = True

        # 3. Numeric validity & Arithmetic consistency
        total = fields.get("total_amount", 0.0)
        subtotal = fields.get("subtotal", 0.0)
        tax = fields.get("tax", 0.0)

        if total <= 0:
            errors.append(f"Invalid total amount: {total}")
            checks["total_positive"] = False
        else:
            checks["total_positive"] = True

        if subtotal > 0 and tax >= 0:
            expected_total = round(subtotal + tax, 2)
            if abs(expected_total - round(total, 2)) > 0.02:
                warnings.append(f"Arithmetic discrepancy: subtotal ({subtotal}) + tax ({tax}) != total ({total})")
                checks["arithmetic_consistent"] = False
            else:
                checks["arithmetic_consistent"] = True

        return {
            "valid": len(errors) == 0 and checks.get("due_date_valid", False),
            "errors": errors,
            "warnings": warnings,
            "checks": checks,
            "requires_clarification": not checks.get("due_date_valid", False)
        }
