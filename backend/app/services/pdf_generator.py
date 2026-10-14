import fitz  # PyMuPDF
from pathlib import Path
from backend.app.core.config import INVOICES_DIR

def create_invoice_pdf(
    filename: str,
    vendor: str,
    invoice_number: str,
    invoice_date: str,
    due_date: str,
    currency: str,
    subtotal: float,
    tax: float,
    total_amount: float,
    items: list,
    notes: str = ""
) -> Path:
    """Generates a professional, crisp synthetic PDF invoice using PyMuPDF."""
    filepath = INVOICES_DIR / filename
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)  # A4 size in points

    # Palette
    primary_color = (0.1, 0.2, 0.45)   # Navy blue
    gray_line = (0.8, 0.8, 0.85)
    dark_gray = (0.2, 0.2, 0.25)
    light_bg = (0.95, 0.96, 0.98)

    # Header Background
    page.draw_rect(fitz.Rect(0, 0, 595, 110), fill=primary_color, color=None)

    # Header Titles
    page.insert_text(fitz.Point(50, 50), "INVOICE", fontname="helv", fontsize=28, color=(1, 1, 1))
    page.insert_text(fitz.Point(50, 75), f"Official Commercial Invoice • {vendor}", fontname="helv", fontsize=11, color=(0.85, 0.9, 1))
    page.insert_text(fitz.Point(400, 50), f"#{invoice_number}", fontname="helv", fontsize=16, color=(1, 1, 1))
    page.insert_text(fitz.Point(400, 72), f"Status: ISSUED", fontname="helv", fontsize=10, color=(0.8, 1, 0.8))

    # Vendor & Bill To Blocks
    # Left Block: Vendor
    page.insert_text(fitz.Point(50, 140), "FROM:", fontname="helv", fontsize=9, color=(0.5, 0.5, 0.5))
    page.insert_text(fitz.Point(50, 158), vendor, fontname="helv", fontsize=14, color=dark_gray)
    page.insert_text(fitz.Point(50, 175), "100 Enterprise Way, Suite 400", fontname="helv", fontsize=10, color=dark_gray)
    page.insert_text(fitz.Point(50, 190), "San Francisco, CA 94105", fontname="helv", fontsize=10, color=dark_gray)
    page.insert_text(fitz.Point(50, 205), f"billing@{vendor.lower().replace(' ', '')}.com", fontname="helv", fontsize=10, color=primary_color)

    # Right Block: Metadata Details
    meta_box = fitz.Rect(340, 125, 545, 220)
    page.draw_rect(meta_box, fill=light_bg, color=gray_line, width=1)
    page.insert_text(fitz.Point(355, 148), "Invoice Number:", fontname="helv", fontsize=10, color=(0.4, 0.4, 0.4))
    page.insert_text(fitz.Point(460, 148), invoice_number, fontname="helv", fontsize=10, color=dark_gray)

    page.insert_text(fitz.Point(355, 168), "Invoice Date:", fontname="helv", fontsize=10, color=(0.4, 0.4, 0.4))
    page.insert_text(fitz.Point(460, 168), invoice_date, fontname="helv", fontsize=10, color=dark_gray)

    page.insert_text(fitz.Point(355, 188), "Due Date:", fontname="helv", fontsize=10, color=(0.4, 0.4, 0.4))
    page.insert_text(fitz.Point(460, 188), due_date, fontname="helv", fontsize=10, color=dark_gray)

    page.insert_text(fitz.Point(355, 208), "Currency:", fontname="helv", fontsize=10, color=(0.4, 0.4, 0.4))
    page.insert_text(fitz.Point(460, 208), currency, fontname="helv", fontsize=10, color=dark_gray)

    # Items Table Header
    y_table = 250
    page.draw_rect(fitz.Rect(50, y_table, 545, y_table + 25), fill=light_bg, color=gray_line, width=1)
    page.insert_text(fitz.Point(60, y_table + 17), "Description", fontname="helv", fontsize=10, color=dark_gray)
    page.insert_text(fitz.Point(330, y_table + 17), "Qty", fontname="helv", fontsize=10, color=dark_gray)
    page.insert_text(fitz.Point(390, y_table + 17), "Unit Price", fontname="helv", fontsize=10, color=dark_gray)
    page.insert_text(fitz.Point(475, y_table + 17), "Amount", fontname="helv", fontsize=10, color=dark_gray)

    y_curr = y_table + 45
    for item in items:
        desc = item.get("desc", "")
        qty = str(item.get("qty", 1))
        unit = f"{currency} {item.get('unit_price', 0.0):,.2f}"
        total = f"{currency} {item.get('total', 0.0):,.2f}"

        page.insert_text(fitz.Point(60, y_curr), desc, fontname="helv", fontsize=10, color=dark_gray)
        page.insert_text(fitz.Point(335, y_curr), qty, fontname="helv", fontsize=10, color=dark_gray)
        page.insert_text(fitz.Point(390, y_curr), unit, fontname="helv", fontsize=10, color=dark_gray)
        page.insert_text(fitz.Point(475, y_curr), total, fontname="helv", fontsize=10, color=dark_gray)

        # Underline
        page.draw_line(fitz.Point(50, y_curr + 8), fitz.Point(545, y_curr + 8), color=gray_line, width=0.5)
        y_curr += 28

    # Totals Section
    y_totals = max(y_curr + 20, 420)
    page.draw_line(fitz.Point(340, y_totals), fitz.Point(545, y_totals), color=gray_line, width=1)
    
    page.insert_text(fitz.Point(350, y_totals + 20), "Subtotal:", fontname="helv", fontsize=10, color=(0.4, 0.4, 0.4))
    page.insert_text(fitz.Point(460, y_totals + 20), f"{currency} {subtotal:,.2f}", fontname="helv", fontsize=10, color=dark_gray)

    page.insert_text(fitz.Point(350, y_totals + 40), "Tax (GST/VAT):", fontname="helv", fontsize=10, color=(0.4, 0.4, 0.4))
    page.insert_text(fitz.Point(460, y_totals + 40), f"{currency} {tax:,.2f}", fontname="helv", fontsize=10, color=dark_gray)

    # Highlight Total Box
    total_box = fitz.Rect(340, y_totals + 55, 545, y_totals + 90)
    page.draw_rect(total_box, fill=light_bg, color=primary_color, width=1.5)
    page.insert_text(fitz.Point(350, y_totals + 78), "Total Amount:", fontname="helv", fontsize=12, color=primary_color)
    page.insert_text(fitz.Point(450, y_totals + 78), f"{currency} {total_amount:,.2f}", fontname="helv", fontsize=13, color=primary_color)

    # Notes & Policy footer
    if notes:
        page.insert_text(fitz.Point(50, y_totals + 40), "Notes & Payment Terms:", fontname="helv", fontsize=10, color=(0.3, 0.3, 0.3))
        page.insert_text(fitz.Point(50, y_totals + 60), notes, fontname="helv", fontsize=9, color=(0.4, 0.4, 0.4))

    # Security Stamp / Verification watermark
    page.insert_text(fitz.Point(50, 780), f"CentrAlign Verified Synthetic Document • Generated for Autonomous Agent Test Suite", fontname="helv", fontsize=8, color=(0.6, 0.6, 0.6))
    page.insert_text(fitz.Point(50, 795), f"Document ID: {filename} • Hash SHA256 verified", fontname="helv", fontsize=8, color=(0.6, 0.6, 0.6))

    doc.save(str(filepath))
    doc.close()
    return filepath

def generate_all_demo_invoices():
    """Generates all test invoices required for scenarios."""
    INVOICES_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Acme Corp Older Invoice (2026-08-15)
    create_invoice_pdf(
        filename="acme_invoice_2026_08_15.pdf",
        vendor="Acme Corp",
        invoice_number="ACM-2026-001",
        invoice_date="2026-08-15",
        due_date="2026-09-15",
        currency="USD",
        subtotal=4000.00,
        tax=500.00,
        total_amount=4500.00,
        items=[
            {"desc": "Cloud Infrastructure - August", "qty": 1, "unit_price": 4000.00, "total": 4000.00}
        ],
        notes="Standard Net 30 terms. Electronic payment via wire."
    )

    # 2. Acme Corp Mid-term Invoice (2026-09-10)
    create_invoice_pdf(
        filename="acme_invoice_2026_09_10.pdf",
        vendor="Acme Corp",
        invoice_number="ACM-2026-002",
        invoice_date="2026-09-10",
        due_date="2026-10-10",
        currency="USD",
        subtotal=7200.00,
        tax=1000.00,
        total_amount=8200.00,
        items=[
            {"desc": "Professional Services & API Integration", "qty": 40, "unit_price": 180.00, "total": 7200.00}
        ],
        notes="Net 30 terms."
    )

    # 3. Acme Corp LATEST Invoice (2026-10-01) - PRIMARY TEST TARGET
    create_invoice_pdf(
        filename="acme_invoice_latest.pdf",
        vendor="Acme Corp",
        invoice_number="ACM-2026-003",
        invoice_date="2026-10-01",
        due_date="2026-10-31",
        currency="USD",
        subtotal=10000.00,
        tax=1800.00,
        total_amount=11800.00,
        items=[
            {"desc": "Enterprise Software License - Annual Tier", "qty": 1, "unit_price": 8500.00, "total": 8500.00},
            {"desc": "Dedicated Support & SLAs", "qty": 1, "unit_price": 1500.00, "total": 1500.00}
        ],
        notes="Payment due strictly on or before 2026-10-31. Wire instructions on file."
    )

    # 4. Acme Corp Ambiguous Invoice (Conflicting or missing due date) - SCENARIO C
    create_invoice_pdf(
        filename="acme_invoice_ambiguous.pdf",
        vendor="Acme Corp",
        invoice_number="ACM-2026-AMB",
        invoice_date="2026-09-05",
        due_date="AMBIGUOUS - PENDING CONTRACT AMENDMENT",
        currency="USD",
        subtotal=6500.00,
        tax=850.00,
        total_amount=7350.00,
        items=[
            {"desc": "Quarterly Consulting retainer - Custom Scope", "qty": 1, "unit_price": 6500.00, "total": 6500.00}
        ],
        notes="Notice: Due date is subject to contract schedule addendum. Terms conflict with master agreement."
    )

    # 5. Globex Invoice (for vendor search differentiation)
    create_invoice_pdf(
        filename="globex_invoice_2026_09_28.pdf",
        vendor="Globex Corp",
        invoice_number="GLX-2026-099",
        invoice_date="2026-09-28",
        due_date="2026-10-28",
        currency="USD",
        subtotal=12500.00,
        tax=1700.00,
        total_amount=14200.00,
        items=[
            {"desc": "Industrial Machinery Hardware Lease", "qty": 1, "unit_price": 12500.00, "total": 12500.00}
        ],
        notes="Payment Net 30."
    )
    print("All synthetic invoice PDFs generated successfully!")

if __name__ == "__main__":
    generate_all_demo_invoices()
