from typing import Dict, Any, Optional
import uuid
import datetime
from backend.app.tools.registry import tool_registry
from backend.app.models import TaskNote, CompanyPolicy, ApprovalRequest, ApprovalStatus

@tool_registry.register(
    name="get_task_state",
    description="Retrieve current task execution state, observations, and context memory.",
    input_schema={"type": "object", "properties": {}},
    permission="read"
)
def get_task_state(context: Dict[str, Any]) -> Dict[str, Any]:
    task = context.get("task")
    return {
        "task_id": task.id if task else "unknown",
        "goal": task.goal if task else "",
        "status": task.status.value if task and hasattr(task.status, "value") else str(task.status) if task else "UNKNOWN",
        "scenario": task.scenario if task else "standard",
        "memory_keys": list(context.get("task_memory", {}).keys())
    }

@tool_registry.register(
    name="get_company_policy",
    description="Retrieve internal operating policies, financial authorization thresholds, and data governance rules.",
    input_schema={
        "type": "object",
        "properties": {
            "policy_key": {"type": "string", "description": "Key identifier of the policy (e.g. financial_approval, invoice_retention)"}
        },
        "required": ["policy_key"]
    },
    permission="read"
)
def get_company_policy(context: Dict[str, Any], policy_key: str) -> Dict[str, Any]:
    db = context.get("db_session")
    pol = db.query(CompanyPolicy).filter(CompanyPolicy.key == policy_key).first() if db else None
    if pol:
        return {
            "key": pol.key,
            "title": pol.title,
            "description": pol.description,
            "rule_value": pol.rule_value
        }
    
    # Built-in defaults
    default_policies = {
        "financial_approval": {
            "key": "financial_approval",
            "title": "Financial Record Creation Policy",
            "description": "Creation or modification of vendor invoices in internal finance databases requires human supervisor authorization.",
            "rule_value": "REQUIRES_APPROVAL_ALWAYS"
        },
        "due_date_resolution": {
            "key": "due_date_resolution",
            "title": "Ambiguous Due Date Handling",
            "description": "If an invoice contains ambiguous or missing payment terms, the operator must pause and request human supervisor clarification instead of hallucinating.",
            "rule_value": "PAUSE_AND_CLARIFY"
        }
    }
    return default_policies.get(policy_key, {
        "key": policy_key,
        "title": "General Operating Rule",
        "description": "Adhere strictly to verified facts and auditable evidence.",
        "rule_value": "STRICT_VERIFICATION"
    })

@tool_registry.register(
    name="request_human_approval",
    description="Pause execution and request explicit human authorization or clarification for consequential actions.",
    input_schema={
        "type": "object",
        "properties": {
            "action_name": {"type": "string"},
            "payload": {"type": "object"},
            "reason": {"type": "string"}
        },
        "required": ["action_name", "payload", "reason"]
    },
    permission="read"
)
def request_human_approval(context: Dict[str, Any], action_name: str, payload: Dict[str, Any], reason: str) -> Dict[str, Any]:
    import json
    db = context.get("db_session")
    task = context.get("task")
    
    appr_id = f"appr_{uuid.uuid4().hex[:8]}"
    appr = ApprovalRequest(
        id=appr_id,
        task_id=task.id,
        action_name=action_name,
        payload_json=json.dumps(payload),
        reason=reason,
        status=ApprovalStatus.PENDING,
        created_at=datetime.datetime.utcnow()
    )
    db.add(appr)
    db.commit()
    db.refresh(appr)

    return {
        "approval_id": appr.id,
        "status": "PENDING",
        "message": f"Execution paused. Action '{action_name}' requires human authorization: {reason}"
    }

@tool_registry.register(
    name="record_task_note",
    description="Save an auditable note or decision rationale into task memory and persistent history.",
    input_schema={
        "type": "object",
        "properties": {
            "note": {"type": "string", "description": "Decision or progress note text"}
        },
        "required": ["note"]
    },
    permission="read"
)
def record_task_note(context: Dict[str, Any], note: str) -> Dict[str, Any]:
    db = context.get("db_session")
    task = context.get("task")
    
    task_note = TaskNote(
        id=f"note_{uuid.uuid4().hex[:8]}",
        task_id=task.id,
        note_text=note,
        created_at=datetime.datetime.utcnow()
    )
    db.add(task_note)
    db.commit()

    return {"success": True, "note_id": task_note.id, "note": note}
