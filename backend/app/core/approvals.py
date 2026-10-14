import json
import uuid
import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.app.models import ApprovalRequest, ApprovalStatus, Task, TaskStatus
from backend.app.core.config import settings

class ApprovalManager:
    """Manages consequential action gates, human approval pause, and clarification resumption."""

    @staticmethod
    def requires_approval(tool_name: str, arguments: Dict[str, Any]) -> bool:
        """
        Determines whether an action demands human supervisor authorization.
        Financial creations or updates are consequential actions.
        """
        if settings.AUTO_APPROVE_FINANCIAL_RECORDS:
            return False

        if tool_name in ["finance_create_invoice", "finance_update_invoice"]:
            return True

        return False

    @staticmethod
    def create_approval_request(
        db: Session,
        task: Task,
        action_name: str,
        payload: Dict[str, Any],
        reason: str
    ) -> ApprovalRequest:
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
        task.status = TaskStatus.WAITING_FOR_APPROVAL
        db.commit()
        db.refresh(appr)
        return appr

    @staticmethod
    def handle_decision(
        db: Session,
        approval_id: str,
        decision: str,  # "APPROVED" or "REJECTED"
        decision_by: str = "Human Supervisor",
        clarification_value: Optional[str] = None
    ) -> ApprovalRequest:
        appr = db.query(ApprovalRequest).filter(ApprovalRequest.id == approval_id).first()
        if not appr:
            raise ValueError(f"Approval request '{approval_id}' not found.")

        if appr.status != ApprovalStatus.PENDING:
            raise ValueError(f"Approval request '{approval_id}' is already {appr.status.value}.")

        if decision.upper() == "APPROVED":
            appr.status = ApprovalStatus.APPROVED
            appr.decision_by = decision_by
            appr.decision_at = datetime.datetime.utcnow()

            # If user provided a clarification value (e.g. for ambiguous due date), update payload
            if clarification_value:
                payload = json.loads(appr.payload_json)
                payload["due_date"] = clarification_value
                payload["clarification_provided"] = True
                appr.payload_json = json.dumps(payload)

        elif decision.upper() == "REJECTED":
            appr.status = ApprovalStatus.REJECTED
            appr.decision_by = decision_by
            appr.decision_at = datetime.datetime.utcnow()
        else:
            raise ValueError(f"Invalid approval decision: '{decision}'")

        db.commit()
        db.refresh(appr)
        return appr

approval_manager = ApprovalManager()
