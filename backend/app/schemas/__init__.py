from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from backend.app.models import TaskStatus, StepStatus, ApprovalStatus

# Task Schemas
class TaskCreate(BaseModel):
    goal: str
    scenario: Optional[str] = "standard"  # standard, recoverable_failure, ambiguous_invoice, generalization

class TaskStepResponse(BaseModel):
    id: str
    task_id: str
    step_order: int
    description: str
    status: StepStatus
    tool_name: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class TaskEventResponse(BaseModel):
    id: str
    task_id: str
    event_type: str
    message: str
    details_json: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class ToolExecutionResponse(BaseModel):
    id: str
    task_id: str
    step_id: Optional[str] = None
    tool_name: str
    input_data_json: Optional[str] = None
    output_data_json: Optional[str] = None
    duration_ms: int
    status: str
    error_message: Optional[str] = None
    retry_count: int
    created_at: datetime

    class Config:
        from_attributes = True

class ApprovalResponse(BaseModel):
    id: str
    task_id: str
    action_name: str
    payload_json: str
    reason: str
    status: ApprovalStatus
    decision_by: Optional[str] = None
    decision_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

class ApprovalDecisionRequest(BaseModel):
    decision: str  # "APPROVED" or "REJECTED"
    decision_by: Optional[str] = "Human Supervisor"
    clarification_value: Optional[str] = None  # in case human clarification is provided (e.g. for ambiguous due date)

class VerificationResponse(BaseModel):
    id: str
    task_id: str
    target_type: str
    target_id: str
    verified: bool
    field_results_json: Optional[str] = None
    evidence_json: Optional[str] = None
    details: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class TaskResponse(BaseModel):
    id: str
    goal: str
    status: TaskStatus
    scenario: str
    result_summary: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    steps: List[TaskStepResponse] = []
    events: List[TaskEventResponse] = []
    tool_executions: List[ToolExecutionResponse] = []
    approvals: List[ApprovalResponse] = []
    verifications: List[VerificationResponse] = []

    class Config:
        from_attributes = True

# Invoice Schemas
class InvoiceCreate(BaseModel):
    vendor: str
    invoice_number: str
    invoice_date: str
    due_date: str
    currency: Optional[str] = "USD"
    subtotal: Optional[float] = 0.0
    tax: Optional[float] = 0.0
    total_amount: float
    source_document_id: Optional[str] = None

class InvoiceUpdate(BaseModel):
    vendor: Optional[str] = None
    invoice_date: Optional[str] = None
    due_date: Optional[str] = None
    currency: Optional[str] = None
    subtotal: Optional[float] = None
    tax: Optional[float] = None
    total_amount: Optional[float] = None
    status: Optional[str] = None

class InvoiceResponse(BaseModel):
    id: str
    vendor: str
    invoice_number: str
    invoice_date: str
    due_date: str
    currency: str
    subtotal: float
    tax: float
    total_amount: float
    source_document_id: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class DocumentResponse(BaseModel):
    id: str
    filename: str
    file_path: str
    doc_type: str
    metadata_json: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class SupportTicketResponse(BaseModel):
    id: str
    customer: str
    subject: str
    description: str
    priority: str
    created_at: datetime

    class Config:
        from_attributes = True

class InternalTaskCreate(BaseModel):
    title: str
    description: str
    assigned_to: Optional[str] = "Operations"
    related_ticket_id: Optional[str] = None

class InternalTaskResponse(BaseModel):
    id: str
    title: str
    description: str
    assigned_to: str
    related_ticket_id: Optional[str] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
