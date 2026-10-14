from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from backend.app.db.session import get_db, SessionLocal
from backend.app.models import ApprovalRequest, Task
from backend.app.schemas import ApprovalResponse, ApprovalDecisionRequest
from backend.app.core.approvals import approval_manager
from backend.app.core.orchestrator import TaskOrchestrator

router = APIRouter(prefix="/approvals", tags=["Human Approvals & Clarification"])

@router.get("", response_model=list[ApprovalResponse])
@router.get("/", response_model=list[ApprovalResponse])
def list_all_approvals(db: Session = Depends(get_db)):
    return db.query(ApprovalRequest).order_by(ApprovalRequest.created_at.desc()).all()

@router.get("/{approval_id}", response_model=ApprovalResponse)
def get_approval(approval_id: str, db: Session = Depends(get_db)):
    appr = db.query(ApprovalRequest).filter(ApprovalRequest.id == approval_id).first()
    if not appr:
        raise HTTPException(status_code=404, detail="Approval request not found.")
    return appr

@router.post("/{approval_id}/decision", response_model=ApprovalResponse)
def make_decision(
    approval_id: str,
    payload: ApprovalDecisionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    try:
        appr = approval_manager.handle_decision(
            db=db,
            approval_id=approval_id,
            decision=payload.decision,
            decision_by=payload.decision_by or "Human Supervisor",
            clarification_value=payload.clarification_value
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # If approved, resume the task in background
    if payload.decision.upper() == "APPROVED":
        def _resume(task_id: str):
            bg_db = SessionLocal()
            try:
                orch = TaskOrchestrator(bg_db)
                orch.run_task(task_id)
            finally:
                bg_db.close()

        background_tasks.add_task(_resume, appr.task_id)

    return appr
