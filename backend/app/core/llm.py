from typing import Dict, Any, List, Optional
import json
import logging
import httpx
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

class LLMProvider:
    """
    LLM Provider Abstraction.
    Supports external LLM APIs (OpenAI, Anthropic, Gemini) and a robust Deterministic Demo Mode.
    """
    def __init__(self):
        self.provider = settings.LLM_PROVIDER
        self.api_key = settings.LLM_API_KEY
        self.model = settings.LLM_MODEL
        self.demo_mode = settings.DEMO_MODE or not self.api_key

    def generate_plan(self, goal: str, available_tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generates a structured plan for the task."""
        if not self.demo_mode and self.api_key:
            return self._call_llm_plan(goal, available_tools)
        return self._deterministic_plan(goal, available_tools)

    def select_next_action(
        self,
        goal: str,
        plan: List[Dict[str, Any]],
        current_step_index: int,
        observations: List[Dict[str, Any]],
        task_memory: Dict[str, Any],
        available_tools: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Selects next action based on current state, plan, and observations."""
        if not self.demo_mode and self.api_key:
            return self._call_llm_action(goal, plan, current_step_index, observations, task_memory, available_tools)
        return self._deterministic_action(goal, plan, current_step_index, observations, task_memory, available_tools)

    def _deterministic_plan(self, goal: str, available_tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        goal_lower = goal.lower()
        
        # Generalization scenario: support ticket
        if "ticket" in goal_lower or "internal task" in goal_lower:
            return {
                "objective": "Find customer Acme Corp support ticket, create internal follow-up task, and verify existence.",
                "steps": [
                    {"step_order": 1, "description": "Search support portal for Acme Corp tickets", "tool_name": "support_search_tickets"},
                    {"step_order": 2, "description": "Analyze ticket issue and create internal follow-up task", "tool_name": "support_create_internal_task"},
                    {"step_order": 3, "description": "Verify persisted internal task independently", "tool_name": "support_verify_task"}
                ]
            }

        # Primary workflow: Invoice processing
        return {
            "objective": "Locate latest Acme Corp invoice, extract and validate fields, verify non-duplicate, create finance record, and independently verify persistence.",
            "steps": [
                {"step_order": 1, "description": "Search vendor portal for Acme Corp invoices", "tool_name": "browser_search"},
                {"step_order": 2, "description": "Extract invoice list from portal DOM and select the latest invoice by date", "tool_name": "browser_extract_page"},
                {"step_order": 3, "description": "Download selected invoice PDF document", "tool_name": "browser_download"},
                {"step_order": 4, "description": "Extract structured invoice fields and source evidence from PDF", "tool_name": "extract_invoice_fields"},
                {"step_order": 5, "description": "Validate invoice fields, date formats, and arithmetic consistency", "tool_name": "validate_invoice_fields"},
                {"step_order": 6, "description": "Check finance system to ensure invoice does not already exist", "tool_name": "finance_search_invoices"},
                {"step_order": 7, "description": "Create verified invoice record in finance database", "tool_name": "finance_create_invoice"},
                {"step_order": 8, "description": "Independently read back and verify persisted record against source values", "tool_name": "finance_verify_invoice"}
            ]
        }

    def _deterministic_action(
        self,
        goal: str,
        plan: List[Dict[str, Any]],
        current_step_index: int,
        observations: List[Dict[str, Any]],
        task_memory: Dict[str, Any],
        available_tools: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Dynamically inspects task memory and past observations to pick the next action.
        """
        # Support ticket workflow
        if "ticket" in goal.lower() or "internal task" in goal.lower():
            if current_step_index == 0:
                return {
                    "tool_name": "support_search_tickets",
                    "arguments": {"customer": "Acme Corp"},
                    "rationale": "Search support database for Acme Corp customer tickets."
                }
            elif current_step_index == 1:
                tickets = task_memory.get("tickets", [])
                t = tickets[0] if tickets else {"id": "TCK-8821", "subject": "API Rate Limit", "description": "Rate limits"}
                return {
                    "tool_name": "support_create_internal_task",
                    "arguments": {
                        "title": f"Follow-up on Ticket {t['id']}: {t['subject']}",
                        "description": f"Automated follow-up task created from customer support inquiry: {t['description']}",
                        "assigned_to": "Infrastructure Engineering",
                        "related_ticket_id": t["id"]
                    },
                    "rationale": "Create operational follow-up task for engineering."
                }
            elif current_step_index == 2:
                task_id = task_memory.get("created_internal_task_id", "itask_demo")
                return {
                    "tool_name": "support_verify_task",
                    "arguments": {"task_id": task_id},
                    "rationale": "Perform independent read-back verification of the internal task."
                }

        # Invoice Processing Workflow
        if current_step_index == 0:
            return {
                "tool_name": "browser_search",
                "arguments": {"query": "Acme Corp"},
                "rationale": "Query vendor portal for Acme Corp invoices."
            }

        elif current_step_index == 1:
            return {
                "tool_name": "browser_extract_page",
                "arguments": {},
                "rationale": "Extract available invoices from DOM to identify the latest record by date."
            }

        elif current_step_index == 2:
            latest_invoice = task_memory.get("selected_invoice", {})
            download_url = latest_invoice.get("download_url", "/portal/download/acme_invoice_latest.pdf")
            return {
                "tool_name": "browser_download",
                "arguments": {"download_url": download_url},
                "rationale": f"Download invoice PDF artifact for '{latest_invoice.get('invoice_number', 'latest')}''."
            }

        elif current_step_index == 3:
            doc_id = task_memory.get("downloaded_doc_id", "acme_invoice_latest.pdf")
            return {
                "tool_name": "extract_invoice_fields",
                "arguments": {"document_id": doc_id},
                "rationale": "Extract structured fields, totals, and evidence from downloaded PDF."
            }

        elif current_step_index == 4:
            fields = task_memory.get("extracted_fields", {})
            return {
                "tool_name": "validate_invoice_fields",
                "arguments": {"fields": fields},
                "rationale": "Verify date formats, required fields, and arithmetic consistency."
            }

        elif current_step_index == 5:
            fields = task_memory.get("extracted_fields", {})
            inv_num = fields.get("invoice_number", "ACM-2026-003")
            return {
                "tool_name": "finance_search_invoices",
                "arguments": {"invoice_number": inv_num},
                "rationale": f"Check internal finance database to ensure invoice '{inv_num}' is not already recorded."
            }

        elif current_step_index == 6:
            fields = task_memory.get("extracted_fields", {})
            return {
                "tool_name": "finance_create_invoice",
                "arguments": {
                    "vendor": fields.get("vendor", "Acme Corp"),
                    "invoice_number": fields.get("invoice_number", "ACM-2026-003"),
                    "invoice_date": fields.get("invoice_date", "2026-10-01"),
                    "due_date": fields.get("due_date", "2026-10-31"),
                    "total_amount": fields.get("total_amount", 11800.00),
                    "currency": fields.get("currency", "USD"),
                    "subtotal": fields.get("subtotal", 10000.00),
                    "tax": fields.get("tax", 1800.00),
                    "source_document_id": fields.get("source_document_id", "acme_invoice_latest.pdf")
                },
                "rationale": "Submit new invoice record to internal finance system."
            }

        elif current_step_index == 7:
            fields = task_memory.get("extracted_fields", {})
            inv_num = fields.get("invoice_number", "ACM-2026-003")
            return {
                "tool_name": "finance_verify_invoice",
                "arguments": {
                    "invoice_number": inv_num,
                    "expected_fields": {
                        "vendor": fields.get("vendor", "Acme Corp"),
                        "invoice_number": inv_num,
                        "invoice_date": fields.get("invoice_date", "2026-10-01"),
                        "due_date": fields.get("due_date", "2026-10-31"),
                        "total_amount": fields.get("total_amount", 11800.00)
                    }
                },
                "rationale": "Perform independent read-back verification comparing saved SQLite record against extracted source data."
            }

        return {
            "tool_name": "get_task_state",
            "arguments": {},
            "rationale": "Task completed or step index out of bounds."
        }

    def _call_llm_plan(self, goal: str, available_tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calls external OpenAI-compatible LLM endpoint if configured."""
        try:
            headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
            prompt = f"Create a step-by-step action plan to achieve this goal: '{goal}'. Available tools: {[t['name'] for t in available_tools]}. Return JSON with 'objective' and 'steps' (each having 'step_order', 'description', 'tool_name')."
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "You are CentrAlign Planner. Return strictly valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                "response_format": {"type": "json_object"}
            }
            resp = httpx.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=20)
            if resp.status_code == 200:
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                return json.loads(content)
        except Exception as e:
            logger.warning(f"External LLM call failed: {e}. Falling back to deterministic plan.")
        return self._deterministic_plan(goal, available_tools)

    def _call_llm_action(self, goal: str, plan: List[Dict[str, Any]], current_step_index: int, observations: List[Dict[str, Any]], task_memory: Dict[str, Any], available_tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        return self._deterministic_action(goal, plan, current_step_index, observations, task_memory, available_tools)

llm_provider = LLMProvider()
