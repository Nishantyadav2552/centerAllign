import os
import re
import uuid
import datetime
import urllib.parse
from pathlib import Path
from typing import Dict, Any, List, Optional
import httpx
from PIL import Image, ImageDraw

from backend.app.core.config import settings, SCREENSHOTS_DIR, INVOICES_DIR

class BrowserService:
    """
    Controlled Browser Service for CentrAlign Operator.
    Enforces origin restrictions, sandbox security, DOM extraction, and visual capture.
    Supports in-process ASGI routing when port 8000 is not listening externally.
    """
    def __init__(self, session_id: Optional[str] = None):
        self.session_id = session_id or str(uuid.uuid4())
        self.current_url: Optional[str] = None
        self.current_html: Optional[str] = None
        self.status_code: int = 200

        from fastapi.testclient import TestClient
        from backend.app.main import app
        self.client = TestClient(app, base_url="http://127.0.0.1:8000")

    def _validate_origin(self, url: str):
        parsed = urllib.parse.urlparse(url)
        origin = f"{parsed.scheme}://{parsed.netloc}"
        if not parsed.netloc:
            return
        if not any(origin.startswith(allowed) for allowed in settings.ALLOWED_ORIGINS):
            raise ValueError(f"Navigation to unauthorized origin '{origin}' is blocked by security policy.")

    def open(self, url: str) -> Dict[str, Any]:
        """Opens an allowed page in the controlled demo environment."""
        if not url.startswith("http"):
            base = settings.PORTAL_BASE_URL
            url = urllib.parse.urljoin(base, url)
            
        self._validate_origin(url)
        
        try:
            resp = self.client.get(url)
            self.current_url = str(resp.url)
            self.status_code = resp.status_code
            self.current_html = resp.text

            if resp.status_code == 503:
                return {
                    "url": self.current_url,
                    "status_code": 503,
                    "success": False,
                    "error": "503 Gateway Timeout: Vendor Database Gateway Pool Exhausted. Transient failure.",
                    "recoverable": True
                }
            
            if resp.status_code >= 400:
                return {
                    "url": self.current_url,
                    "status_code": resp.status_code,
                    "success": False,
                    "error": f"HTTP Error {resp.status_code}",
                    "recoverable": False
                }

            return {
                "url": self.current_url,
                "status_code": 200,
                "success": True,
                "page_title": self._extract_title(resp.text)
            }
        except Exception as exc:
            return {
                "url": url,
                "success": False,
                "error": f"Connection error: {str(exc)}",
                "recoverable": True
            }

    def search(self, query: str, scenario: Optional[str] = None) -> Dict[str, Any]:
        """Searches the vendor portal using an accessible query."""
        search_url = f"/portal?q={urllib.parse.quote(query)}"
        if scenario:
            search_url += f"&scenario={scenario}&session_id={self.session_id}"
        
        return self.open(search_url)

    def fill(self, selector: str, value: str) -> Dict[str, Any]:
        """Simulates filling an accessible form field."""
        if not self.current_url:
            raise ValueError("No page is currently open. Call browser_open first.")
        return {
            "success": True,
            "selector": selector,
            "filled_value": value,
            "message": f"Successfully entered '{value}' into field matching '{selector}'."
        }

    def click(self, target_identifier: str) -> Dict[str, Any]:
        """Clicks an accessible button or link."""
        if not self.current_html:
            raise ValueError("No page is currently open.")
        
        if "download" in target_identifier.lower() or ".pdf" in target_identifier.lower():
            match = re.search(r'href="([^"]*(?:download/[^"]+))"', self.current_html)
            if match:
                dl_url = match.group(1)
                return self.download(dl_url)
        
        return {
            "success": True,
            "target": target_identifier,
            "message": f"Clicked target '{target_identifier}'."
        }

    def extract_page(self) -> Dict[str, Any]:
        """Extracts structured invoice rows, metadata, and tables from current page."""
        if not self.current_html:
            return {"error": "No page content available", "invoices": []}
        
        if self.status_code == 503:
            return {
                "error": "503 Gateway Timeout: Vendor Database is currently unavailable.",
                "recoverable": True,
                "invoices": []
            }

        invoices = []
        rows = re.findall(
            r'<tr class="invoice-row" data-vendor="([^"]+)" data-invoice-number="([^"]+)" data-date="([^"]+)">(.*?)</tr>',
            self.current_html,
            re.DOTALL
        )
        for vendor, inv_num, inv_date, row_content in rows:
            due_match = re.search(r'<td>(\d{4}-\d{2}-\d{2}|AMBIGUOUS[^<]*)</td>', row_content)
            due_date = due_match.group(1) if due_match else ""

            amt_match = re.search(r'([A-Z]{3})\s+([\d,]+\.\d{2})', row_content)
            currency = amt_match.group(1) if amt_match else "USD"
            total_amt = float(amt_match.group(2).replace(",", "")) if amt_match else 0.0

            file_match = re.search(r'data-filename="([^"]+)"', row_content)
            filename = file_match.group(1) if file_match else ""

            invoices.append({
                "vendor": vendor,
                "invoice_number": inv_num,
                "invoice_date": inv_date,
                "due_date": due_date,
                "currency": currency,
                "total_amount": total_amt,
                "filename": filename,
                "download_url": f"/portal/download/{filename}"
            })

        tickets = []
        ticket_rows = re.findall(
            r'<tr class="ticket-row" data-id="([^"]+)" data-customer="([^"]+)">(.*?)</tr>',
            self.current_html,
            re.DOTALL
        )
        for t_id, cust, row_content in ticket_rows:
            cols = re.findall(r'<td[^>]*>(.*?)</td>', row_content, re.DOTALL)
            tickets.append({
                "id": t_id,
                "customer": cust,
                "subject": cols[2].strip() if len(cols) > 2 else "",
                "description": cols[3].strip() if len(cols) > 3 else "",
                "created_at": cols[5].strip() if len(cols) > 5 else ""
            })

        return {
            "url": self.current_url,
            "title": self._extract_title(self.current_html),
            "invoice_count": len(invoices),
            "invoices": invoices,
            "tickets": tickets
        }

    def download(self, download_url: str) -> Dict[str, Any]:
        """Downloads invoice PDF artifact and returns secure local reference."""
        parsed = urllib.parse.urlparse(download_url)
        filename = Path(parsed.path).name
        
        dest_path = INVOICES_DIR / filename
        # In demo environment, invoice files are verified in demo directory
        if not dest_path.exists():
            resp = self.client.get(download_url)
            if resp.status_code == 200:
                with open(dest_path, "wb") as f:
                    f.write(resp.content)
            else:
                return {"success": False, "error": f"Failed to download artifact: HTTP {resp.status_code}"}

        return {
            "success": True,
            "filename": filename,
            "document_id": filename,
            "size_bytes": dest_path.stat().st_size if dest_path.exists() else 0,
            "local_artifact_ref": f"doc://{filename}",
            "message": f"Successfully retrieved invoice document '{filename}'."
        }

    def screenshot(self, label: str = "capture") -> Dict[str, Any]:
        """Captures visual evidence for timeline audit."""
        filename = f"screenshot_{label}_{uuid.uuid4().hex[:6]}.png"
        filepath = SCREENSHOTS_DIR / filename

        # 1. Try real Playwright screenshot if live server is reachable
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page(viewport={"width": 1024, "height": 768})
                target_url = self.current_url or settings.PORTAL_BASE_URL
                if target_url.startswith("/"):
                    target_url = urllib.parse.urljoin("http://127.0.0.1:8000", target_url)
                page.goto(target_url, timeout=3000)
                page.screenshot(path=str(filepath))
                browser.close()
                return {
                    "success": True,
                    "screenshot_file": filename,
                    "url": self.current_url,
                    "artifact_path": f"/screenshots/{filename}",
                    "engine": "playwright_chromium"
                }
        except Exception:
            pass

        # 2. Fallback to high-contrast DOM renderer with Pillow
        img = Image.new("RGB", (900, 600), color=(15, 23, 42))
        draw = ImageDraw.Draw(img)

        draw.rectangle([0, 0, 900, 48], fill=(30, 41, 59))
        draw.text((20, 16), f"CentrAlign Browser View • {self.current_url or 'Empty'}", fill=(148, 163, 184))
        draw.text((750, 16), f"Status: {self.status_code}", fill=(52, 211, 153) if self.status_code == 200 else (239, 68, 68))

        draw.text((40, 80), f"Page Title: {self._extract_title(self.current_html or '')}", fill=(241, 245, 249))
        draw.line([40, 110, 860, 110], fill=(51, 65, 85), width=2)

        if self.current_html:
            clean_text = re.sub(r'<[^>]+>', ' ', self.current_html)
            clean_lines = [line.strip() for line in clean_text.splitlines() if line.strip()][:15]
            y = 130
            for line in clean_lines:
                draw.text((40, y), line[:95], fill=(203, 213, 225))
                y += 24
        else:
            draw.text((40, 150), "[No DOM Loaded]", fill=(148, 163, 184))

        img.save(str(filepath), "PNG")

        return {
            "success": True,
            "screenshot_file": filename,
            "url": self.current_url,
            "artifact_path": f"/screenshots/{filename}"
        }

    def _extract_title(self, html: str) -> str:
        match = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE)
        return match.group(1).strip() if match else "Untitled"
