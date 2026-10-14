import enum
import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from backend.app.db.session import Base

class TaskStatus(str, enum.Enum):
    PENDING = "PENDING"
    PLANNING = "PLANNING"
    RUNNING = "RUNNING"
    WAITING_FOR_APPROVAL = "WAITING_FOR_APPROVAL"
    WAITING_FOR_INPUT = "WAITING_FOR_INPUT"
    VERIFYING = "VERIFYING"
    COMPLETED = "COMPLETED"
    PARTIALLY_COMPLETED = "PARTIALLY_COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class StepStatus(str, enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"

class ApprovalStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

class Task(Base):
    __tablename__ = "tasks"

    id = Column(String, primary_key=True, index=True)
    goal = Column(Text, nullable=False)
    status = Column(SQLEnum(TaskStatus), default=TaskStatus.PENDING, nullable=False, index=True)
    scenario = Column(String, default="standard")  # standard, recoverable_failure, ambiguous_invoice, generalization
    result_summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    steps = relationship("TaskStep", back_populates="task", cascade="all, delete-orphan", order_by="TaskStep.step_order")
    events = relationship("TaskEvent", back_populates="task", cascade="all, delete-orphan", order_by="TaskEvent.created_at")
    tool_executions = relationship("ToolExecution", back_populates="task", cascade="all, delete-orphan", order_by="ToolExecution.created_at")
    approvals = relationship("ApprovalRequest", back_populates="task", cascade="all, delete-orphan")
    verifications = relationship("VerificationRecord", back_populates="task", cascade="all, delete-orphan")
    notes = relationship("TaskNote", back_populates="task", cascade="all, delete-orphan")

class TaskStep(Base):
    __tablename__ = "task_steps"

    id = Column(String, primary_key=True, index=True)
    task_id = Column(String, ForeignKey("tasks.id"), nullable=False, index=True)
    step_order = Column(Integer, nullable=False)
    description = Column(String, nullable=False)
    status = Column(SQLEnum(StepStatus), default=StepStatus.PENDING, nullable=False)
    tool_name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    task = relationship("Task", back_populates="steps")

class TaskEvent(Base):
    __tablename__ = "task_events"

    id = Column(String, primary_key=True, index=True)
    task_id = Column(String, ForeignKey("tasks.id"), nullable=False, index=True)
    event_type = Column(String, nullable=False)  # PLAN, TOOL_CALL, TOOL_RESULT, RETRY, APPROVAL_REQUESTED, VERIFICATION, STATE_CHANGE, ERROR
    message = Column(Text, nullable=False)
    details_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    task = relationship("Task", back_populates="events")

class ToolExecution(Base):
    __tablename__ = "tool_executions"

    id = Column(String, primary_key=True, index=True)
    task_id = Column(String, ForeignKey("tasks.id"), nullable=False, index=True)
    step_id = Column(String, nullable=True)
    tool_name = Column(String, nullable=False, index=True)
    input_data_json = Column(Text, nullable=True)
    output_data_json = Column(Text, nullable=True)
    duration_ms = Column(Integer, default=0)
    status = Column(String, nullable=False)  # SUCCESS, FAILURE, TIMEOUT, RETRIED
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    task = relationship("Task", back_populates="tool_executions")

class InvoiceRecord(Base):
    __tablename__ = "invoice_records"

    id = Column(String, primary_key=True, index=True)
    vendor = Column(String, nullable=False, index=True)
    invoice_number = Column(String, nullable=False, unique=True, index=True)
    invoice_date = Column(String, nullable=False)
    due_date = Column(String, nullable=False)
    currency = Column(String, default="USD")
    subtotal = Column(Float, default=0.0)
    tax = Column(Float, default=0.0)
    total_amount = Column(Float, nullable=False)
    source_document_id = Column(String, nullable=True)
    status = Column(String, default="RECORDED")  # RECORDED, VERIFIED, UPDATED
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class ApprovalRequest(Base):
    __tablename__ = "approvals"

    id = Column(String, primary_key=True, index=True)
    task_id = Column(String, ForeignKey("tasks.id"), nullable=False, index=True)
    action_name = Column(String, nullable=False)
    payload_json = Column(Text, nullable=False)
    reason = Column(Text, nullable=False)
    status = Column(SQLEnum(ApprovalStatus), default=ApprovalStatus.PENDING, nullable=False)
    decision_by = Column(String, nullable=True)
    decision_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    task = relationship("Task", back_populates="approvals")

class VerificationRecord(Base):
    __tablename__ = "verification_records"

    id = Column(String, primary_key=True, index=True)
    task_id = Column(String, ForeignKey("tasks.id"), nullable=False, index=True)
    target_type = Column(String, default="invoice")  # invoice, ticket, etc.
    target_id = Column(String, nullable=False)
    verified = Column(Boolean, default=False)
    field_results_json = Column(Text, nullable=True)  # {field: {expected, actual, match: bool}}
    evidence_json = Column(Text, nullable=True)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    task = relationship("Task", back_populates="verifications")

class DocumentRecord(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    doc_type = Column(String, default="pdf")
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class CompanyPolicy(Base):
    __tablename__ = "company_policies"

    id = Column(String, primary_key=True, index=True)
    key = Column(String, unique=True, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    rule_value = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class TaskNote(Base):
    __tablename__ = "task_notes"

    id = Column(String, primary_key=True, index=True)
    task_id = Column(String, ForeignKey("tasks.id"), nullable=False, index=True)
    note_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    task = relationship("Task", back_populates="notes")

class SupportTicket(Base):
    __tablename__ = "support_tickets"

    id = Column(String, primary_key=True, index=True)
    customer = Column(String, nullable=False, index=True)
    subject = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    priority = Column(String, default="NORMAL")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class InternalTask(Base):
    __tablename__ = "internal_tasks"

    id = Column(String, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    assigned_to = Column(String, default="Operations")
    related_ticket_id = Column(String, nullable=True)
    status = Column(String, default="OPEN")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
