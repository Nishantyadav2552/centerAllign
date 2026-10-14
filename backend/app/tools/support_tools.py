from typing import Dict, Any, List, Optional
import uuid
import datetime
from backend.app.tools.registry import tool_registry
from backend.app.models import SupportTicket, InternalTask

@tool_registry.register(
    name="support_search_tickets",
    description="Search customer support tickets database for tickets matching a customer or issue keyword.",
    input_schema={
        "type": "object",
        "properties": {
            "customer": {"type": "string", "description": "Customer name keyword (e.g. Acme Corp)"}
        },
        "required": ["customer"]
    },
    permission="read"
)
def support_search_tickets(context: Dict[str, Any], customer: str) -> Dict[str, Any]:
    db = context.get("db_session")
    tickets = db.query(SupportTicket).filter(SupportTicket.customer.ilike(f"%{customer}%")).all()
    
    # If empty, return initial mock tickets
    if not tickets:
        from backend.app.api.portal import MOCK_TICKETS
        matches = [t for t in MOCK_TICKETS if customer.lower() in t["customer"].lower()]
        return {"tickets": matches, "count": len(matches)}

    return {
        "tickets": [
            {
                "id": t.id,
                "customer": t.customer,
                "subject": t.subject,
                "description": t.description,
                "priority": t.priority,
                "created_at": t.created_at.isoformat() if t.created_at else None
            }
            for t in tickets
        ],
        "count": len(tickets)
    }

@tool_registry.register(
    name="support_create_internal_task",
    description="Create an internal follow-up task in the operations system for an engineering or operations team.",
    input_schema={
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "description": {"type": "string"},
            "assigned_to": {"type": "string", "default": "Infrastructure Engineering"},
            "related_ticket_id": {"type": "string"}
        },
        "required": ["title", "description"]
    },
    requires_approval=False,
    permission="write"
)
def support_create_internal_task(
    context: Dict[str, Any],
    title: str,
    description: str,
    assigned_to: str = "Infrastructure Engineering",
    related_ticket_id: Optional[str] = None
) -> Dict[str, Any]:
    db = context.get("db_session")
    task_id = f"itask_{uuid.uuid4().hex[:8]}"
    internal_task = InternalTask(
        id=task_id,
        title=title,
        description=description,
        assigned_to=assigned_to,
        related_ticket_id=related_ticket_id,
        status="OPEN",
        created_at=datetime.datetime.utcnow()
    )
    db.add(internal_task)
    db.commit()
    db.refresh(internal_task)

    return {
        "success": True,
        "task_id": internal_task.id,
        "title": internal_task.title,
        "assigned_to": internal_task.assigned_to,
        "status": internal_task.status,
        "message": f"Internal task '{internal_task.id}' created successfully."
    }

@tool_registry.register(
    name="support_verify_task",
    description="Independently verify that an internal follow-up task was recorded in the database.",
    input_schema={
        "type": "object",
        "properties": {
            "task_id": {"type": "string"}
        },
        "required": ["task_id"]
    },
    permission="read"
)
def support_verify_task(context: Dict[str, Any], task_id: str) -> Dict[str, Any]:
    db = context.get("db_session")
    rec = db.query(InternalTask).filter(InternalTask.id == task_id).first()
    if not rec:
        return {"verified": False, "error": f"Internal task '{task_id}' not found."}
    
    return {
        "verified": True,
        "task_id": rec.id,
        "title": rec.title,
        "assigned_to": rec.assigned_to,
        "status": rec.status
    }
