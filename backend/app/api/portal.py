from fastapi import APIRouter, Request, Query, HTTPException, Response
from fastapi.responses import HTMLResponse, FileResponse
from typing import Optional
from pathlib import Path
from backend.app.core.config import INVOICES_DIR

router = APIRouter(prefix="/portal", tags=["Demo Portal"])

# In-memory transient failure tracker for demo scenario B
simulated_failure_counts = {}

MOCK_INVOICES = [
    {
        "id": "inv_1",
        "vendor": "Acme Corp",
        "invoice_number": "ACM-2026-001",
        "invoice_date": "2026-08-15",
        "due_date": "2026-09-15",
        "currency": "USD",
        "total_amount": 4500.00,
        "filename": "acme_invoice_2026_08_15.pdf",
        "status": "PAID"
    },
    {
        "id": "inv_2",
        "vendor": "Acme Corp",
        "invoice_number": "ACM-2026-002",
        "invoice_date": "2026-09-10",
        "due_date": "2026-10-10",
        "currency": "USD",
        "total_amount": 8200.00,
        "filename": "acme_invoice_2026_09_10.pdf",
        "status": "PAID"
    },
    {
        "id": "inv_3",
        "vendor": "Acme Corp",
        "invoice_number": "ACM-2026-003",
        "invoice_date": "2026-10-01",
        "due_date": "2026-10-31",
        "currency": "USD",
        "total_amount": 11800.00,
        "filename": "acme_invoice_latest.pdf",
        "status": "ISSUED"
    },
    {
        "id": "inv_4",
        "vendor": "Acme Corp",
        "invoice_number": "ACM-2026-AMB",
        "invoice_date": "2026-09-05",
        "due_date": "AMBIGUOUS - PENDING CONTRACT AMENDMENT",
        "currency": "USD",
        "total_amount": 7350.00,
        "filename": "acme_invoice_ambiguous.pdf",
        "status": "ISSUED"
    },
    {
        "id": "inv_5",
        "vendor": "Globex Corp",
        "invoice_number": "GLX-2026-099",
        "invoice_date": "2026-09-28",
        "due_date": "2026-10-28",
        "currency": "USD",
        "total_amount": 14200.00,
        "filename": "globex_invoice_2026_09_28.pdf",
        "status": "ISSUED"
    }
]

MOCK_TICKETS = [
    {
        "id": "TCK-8821",
        "customer": "Acme Corp",
        "subject": "API Rate Limit exceeded during month-end batch",
        "description": "Customer Acme Corp reported repeated 429 Too Many Requests errors during their monthly reconciliation sync. Needs internal follow-up with infrastructure engineering to adjust quota.",
        "priority": "HIGH",
        "created_at": "2026-10-12 14:30:00"
    },
    {
        "id": "TCK-8819",
        "customer": "Globex Corp",
        "subject": "Inquiry on enterprise SLA terms",
        "description": "Customer inquired about response time commitments under 24/7 contract tier.",
        "priority": "NORMAL",
        "created_at": "2026-10-11 09:15:00"
    }
]

@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
def get_vendor_portal(
    q: Optional[str] = Query(None, description="Search query"),
    scenario: Optional[str] = Query(None, description="Simulate scenario (e.g. recoverable_failure)"),
    session_id: Optional[str] = Query(None, description="Task session id")
):
    # Handle Scenario B: Recoverable failure on first attempt
    if scenario == "recoverable_failure" or q == "sim_fail":
        key = session_id or "global"
        attempts = simulated_failure_counts.get(key, 0)
        simulated_failure_counts[key] = attempts + 1
        if attempts == 0:
            return HTMLResponse(
                content="""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>503 Service Unavailable - Vendor Gateway</title>
                    <style>
                        body { font-family: system-ui, sans-serif; background: #0f172a; color: #f8fafc; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }
                        .error-card { background: #1e293b; border: 1px solid #ef4444; padding: 2rem; border-radius: 8px; max-width: 500px; text-align: center; }
                        h1 { color: #ef4444; margin-top: 0; }
                        p { color: #94a3b8; font-size: 0.95rem; }
                        code { background: #0f172a; padding: 0.2rem 0.4rem; border-radius: 4px; color: #fca5a5; }
                    </style>
                </head>
                <body>
                    <div class="error-card" id="gateway-error-banner">
                        <h1>503 Gateway Timeout</h1>
                        <p>Transient upstream failure: <code>VendorSearchEngine.DatabaseGatewayPoolExhausted</code></p>
                        <p>The vendor database service temporarily did not respond. Please retry your request.</p>
                    </div>
                </body>
                </html>
                """,
                status_code=503
            )

    # Filter invoices
    results = MOCK_INVOICES
    if q:
        query_lower = q.lower().strip()
        results = [
            inv for inv in MOCK_INVOICES
            if query_lower in inv["vendor"].lower()
            or query_lower in inv["invoice_number"].lower()
            or query_lower in inv["invoice_date"]
        ]

    # Render clean, accessible HTML table with stable IDs and data attributes
    rows_html = ""
    for inv in results:
        rows_html += f"""
        <tr class="invoice-row" data-vendor="{inv['vendor']}" data-invoice-number="{inv['invoice_number']}" data-date="{inv['invoice_date']}">
            <td class="font-mono text-blue-400 font-semibold">{inv['invoice_number']}</td>
            <td class="font-medium text-slate-200">{inv['vendor']}</td>
            <td>{inv['invoice_date']}</td>
            <td>{inv['due_date']}</td>
            <td class="font-bold text-slate-100">{inv['currency']} {inv['total_amount']:,.2f}</td>
            <td><span class="badge {inv['status'].lower()}">{inv['status']}</span></td>
            <td>
                <a href="/portal/download/{inv['filename']}" 
                   class="btn-download" 
                   data-invoice-number="{inv['invoice_number']}"
                   data-filename="{inv['filename']}"
                   role="button">
                   Download PDF
                </a>
            </td>
        </tr>
        """

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Acme Vendor Enterprise Portal</title>
        <style>
            :root {{
                --bg: #0b1120;
                --panel: #1e293b;
                --border: #334155;
                --text: #f1f5f9;
                --muted: #94a3b8;
                --accent: #3b82f6;
                --accent-hover: #2563eb;
            }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                background-color: var(--bg);
                color: var(--text);
                margin: 0;
                padding: 2rem;
            }}
            .header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                border-bottom: 1px solid var(--border);
                padding-bottom: 1.5rem;
                margin-bottom: 2rem;
            }}
            .logo-text {{
                font-size: 1.5rem;
                font-weight: 700;
                letter-spacing: -0.02em;
                color: #60a5fa;
            }}
            .search-bar {{
                display: flex;
                gap: 0.75rem;
                margin-bottom: 1.5rem;
            }}
            input[type="text"] {{
                background: var(--panel);
                border: 1px solid var(--border);
                color: white;
                padding: 0.6rem 1rem;
                border-radius: 6px;
                font-size: 0.95rem;
                width: 320px;
            }}
            button, .btn-search {{
                background: var(--accent);
                color: white;
                border: none;
                padding: 0.6rem 1.2rem;
                border-radius: 6px;
                cursor: pointer;
                font-weight: 600;
            }}
            button:hover, .btn-search:hover {{ background: var(--accent-hover); }}
            table {{
                width: 100%;
                border-collapse: collapse;
                background: var(--panel);
                border-radius: 8px;
                overflow: hidden;
                border: 1px solid var(--border);
            }}
            th, td {{
                padding: 0.9rem 1.2rem;
                text-align: left;
                border-bottom: 1px solid var(--border);
                font-size: 0.9rem;
            }}
            th {{
                background: #0f172a;
                color: var(--muted);
                text-transform: uppercase;
                font-size: 0.75rem;
                letter-spacing: 0.05em;
            }}
            .badge {{
                padding: 0.2rem 0.5rem;
                border-radius: 4px;
                font-size: 0.75rem;
                font-weight: 600;
            }}
            .badge.paid {{ background: #064e3b; color: #34d399; }}
            .badge.issued {{ background: #1e3a8a; color: #93c5fd; }}
            .btn-download {{
                background: #334155;
                color: #e2e8f0;
                text-decoration: none;
                padding: 0.35rem 0.75rem;
                border-radius: 4px;
                font-size: 0.8rem;
                display: inline-block;
            }}
            .btn-download:hover {{ background: #475569; }}
        </style>
    </head>
    <body>
        <div class="header">
            <div>
                <div class="logo-text">Acme Vendor Exchange</div>
                <div style="color: var(--muted); font-size: 0.85rem; margin-top: 0.25rem;">Enterprise Supplier Documents & Billing Portal</div>
            </div>
            <div style="font-size: 0.85rem; color: #10b981;">● Gateway Live (Controlled Test Environment)</div>
        </div>

        <form method="GET" action="/portal" class="search-bar">
            <input type="text" id="vendor-search-input" name="q" value="{q or ''}" placeholder="Search by vendor, invoice #, or date..." role="searchbox" />
            <button type="submit" id="vendor-search-btn" class="btn-search">Search Invoices</button>
            {'<a href="/portal" style="color: #94a3b8; align-self: center; text-decoration: none; font-size: 0.85rem;">Clear</a>' if q else ''}
        </form>

        <div id="results-count" style="margin-bottom: 1rem; color: var(--muted); font-size: 0.85rem;">
            Showing {len(results)} invoice(s)
        </div>

        <table id="invoices-table" role="table">
            <thead>
                <tr>
                    <th>Invoice #</th>
                    <th>Vendor</th>
                    <th>Issue Date</th>
                    <th>Due Date</th>
                    <th>Total Amount</th>
                    <th>Status</th>
                    <th>Action</th>
                </tr>
            </thead>
            <tbody id="invoices-tbody">
                {rows_html if rows_html else '<tr><td colspan="7" style="text-align: center; color: var(--muted);">No matching invoices found.</td></tr>'}
            </tbody>
        </table>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

@router.get("/download/{filename}")
def download_invoice(filename: str):
    """Secure endpoint allowing download of permitted demo invoices."""
    # Prevent path traversal
    safe_name = Path(filename).name
    filepath = INVOICES_DIR / safe_name
    if not filepath.exists() or not filepath.is_file():
        raise HTTPException(status_code=404, detail=f"Invoice document '{safe_name}' not found.")
    return FileResponse(
        path=str(filepath),
        filename=safe_name,
        media_type="application/pdf"
    )

@router.get("/support", response_class=HTMLResponse)
def get_support_portal(customer: Optional[str] = Query(None)):
    """Mock Support Portal for the Generalization Task."""
    tickets = MOCK_TICKETS
    if customer:
        cust_lower = customer.lower().strip()
        tickets = [t for t in MOCK_TICKETS if cust_lower in t["customer"].lower()]

    rows_html = ""
    for t in tickets:
        rows_html += f"""
        <tr class="ticket-row" data-id="{t['id']}" data-customer="{t['customer']}">
            <td class="font-mono text-blue-400 font-semibold">{t['id']}</td>
            <td>{t['customer']}</td>
            <td class="font-medium text-slate-100">{t['subject']}</td>
            <td style="max-width: 320px; font-size: 0.85rem; color: #94a3b8;">{t['description']}</td>
            <td><span class="badge {'paid' if t['priority']=='NORMAL' else 'issued'}">{t['priority']}</span></td>
            <td>{t['created_at']}</td>
        </tr>
        """

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Internal Customer Support Desk</title>
        <style>
            body {{ font-family: sans-serif; background: #0b1120; color: #f1f5f9; padding: 2rem; }}
            table {{ width: 100%; border-collapse: collapse; background: #1e293b; border: 1px solid #334155; }}
            th, td {{ padding: 0.8rem 1rem; border-bottom: 1px solid #334155; text-align: left; font-size: 0.9rem; }}
            th {{ background: #0f172a; color: #94a3b8; }}
        </style>
    </head>
    <body>
        <h2>Customer Support Ticket Center</h2>
        <table id="tickets-table">
            <thead>
                <tr>
                    <th>Ticket ID</th>
                    <th>Customer</th>
                    <th>Subject</th>
                    <th>Description</th>
                    <th>Priority</th>
                    <th>Created At</th>
                </tr>
            </thead>
            <tbody>{rows_html}</tbody>
        </table>
    </body>
    </html>
    """
    return HTMLResponse(content=html)
