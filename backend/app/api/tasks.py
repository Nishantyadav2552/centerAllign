import asyncio
import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.app.db.session import get_db, SessionLocal
from backend.app.models import Task, TaskEvent, TaskStep, TaskStatus, ApprovalRequest, VerificationRecord
from backend.app.schemas import (
    TaskCreate, TaskResponse, TaskEventResponse, ApprovalResponse, VerificationResponse
)
from backend.app.core.orchestrator import TaskOrchestrator

router = APIRouter(prefix="/tasks", tags=["Task Lifecycle & Orchestration"])

@router.post("", response_model=TaskResponse, status_code=201)
@router.post("/", response_model=TaskResponse, status_code=201)
def create_task(
    payload: TaskCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    orchestrator = TaskOrchestrator(db)
    task = orchestrator.create_task(goal=payload.goal, scenario=payload.scenario or "standard")
    
    # Run task in background or immediately
    def _execute_async(task_id: str):
        bg_db = SessionLocal()
        try:
            bg_orchestrator = TaskOrchestrator(bg_db)
            bg_orchestrator.run_task(task_id)
        finally:
            bg_db.close()

    background_tasks.add_task(_execute_async, task.id)
    return task

@router.get("", response_model=List[TaskResponse])
@router.get("/", response_model=List[TaskResponse])
def list_tasks(db: Session = Depends(get_db)):
    return db.query(Task).order_by(Task.created_at.desc()).all()

@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: str, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found.")
    return task

@router.post("/{task_id}/run", response_model=TaskResponse)
def run_task(task_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found.")
    
    def _execute_async(tid: str):
        bg_db = SessionLocal()
        try:
            bg_orchestrator = TaskOrchestrator(bg_db)
            bg_orchestrator.run_task(tid)
        finally:
            bg_db.close()

    background_tasks.add_task(_execute_async, task.id)
    return task

@router.post("/{task_id}/cancel", response_model=TaskResponse)
def cancel_task(task_id: str, db: Session = Depends(get_db)):
    orchestrator = TaskOrchestrator(db)
    try:
        return orchestrator.cancel_task(task_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{task_id}/events", response_model=List[TaskEventResponse])
def get_task_events(task_id: str, db: Session = Depends(get_db)):
    return db.query(TaskEvent).filter(TaskEvent.task_id == task_id).order_by(TaskEvent.created_at.asc()).all()

@router.get("/{task_id}/events/stream")
async def stream_task_events(task_id: str):
    """Server-Sent Events (SSE) live progress stream."""
    async def event_generator():
        last_event_time = None
        while True:
            db = SessionLocal()
            try:
                task = db.query(Task).filter(Task.id == task_id).first()
                if not task:
                    break

                query = db.query(TaskEvent).filter(TaskEvent.task_id == task_id)
                if last_event_time:
                    query = query.filter(TaskEvent.created_at > last_event_time)
                new_events = query.order_by(TaskEvent.created_at.asc()).all()

                for evt in new_events:
                    last_event_time = evt.created_at
                    data = {
                        "id": evt.id,
                        "task_id": evt.task_id,
                        "event_type": evt.event_type,
                        "message": evt.message,
                        "details": json.loads(evt.details_json) if evt.details_json else None,
                        "task_status": task.status.value,
                        "created_at": evt.created_at.isoformat()
                    }
                    yield f"data: {json.dumps(data)}\n\n"

                if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                    yield f"data: {json.dumps({'event_type': 'DONE', 'task_status': task.status.value})}\n\n"
                    break
            finally:
                db.close()
            await asyncio.sleep(0.5)

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.get("/{task_id}/approvals", response_model=List[ApprovalResponse])
def get_task_approvals(task_id: str, db: Session = Depends(get_db)):
    return db.query(ApprovalRequest).filter(ApprovalRequest.task_id == task_id).all()

@router.get("/{task_id}/report")
def get_task_report(task_id: str, db: Session = Depends(get_db)):
    """Produces the evidence-backed completion report."""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    steps = db.query(TaskStep).filter(TaskStep.task_id == task_id).order_by(TaskStep.step_order).all()
    verifications = db.query(VerificationRecord).filter(VerificationRecord.task_id == task_id).all()
    events = db.query(TaskEvent).filter(TaskEvent.task_id == task_id).all()

    return {
        "task_id": task.id,
        "goal": task.goal,
        "status": task.status.value,
        "scenario": task.scenario,
        "summary": task.result_summary,
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        "steps_count": len(steps),
        "steps_completed": len([s for s in steps if s.status == "COMPLETED"]),
        "events_count": len(events),
        "verifications": [
            {
                "target_id": v.target_id,
                "verified": v.verified,
                "field_results": json.loads(v.field_results_json) if v.field_results_json else {},
                "evidence": json.loads(v.evidence_json) if v.evidence_json else {},
                "details": v.details
            }
            for v in verifications
        ]
    }
