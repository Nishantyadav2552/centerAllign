import json
import uuid
import time
import datetime
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.models import (
    Task, TaskStep, TaskEvent, ToolExecution, TaskStatus, StepStatus,
    ApprovalRequest, ApprovalStatus, VerificationRecord
)
from backend.app.core.llm import llm_provider
from backend.app.core.executor import tool_executor, ExecutionResult
from backend.app.core.recovery import recovery_manager
from backend.app.core.verification import verification_engine
from backend.app.core.approvals import approval_manager
from backend.app.services.browser_service import BrowserService
from backend.app.tools.registry import tool_registry

logger = logging.getLogger(__name__)

class TaskOrchestrator:
    """
    Central Autonomous Execution Engine for CentrAlign Operator.
    Implements: GOAL → UNDERSTAND → PLAN → EXECUTE → OBSERVE → ADAPT → VERIFY → COMPLETE
    """

    def __init__(self, db: Session):
        self.db = db

    def _log_event(self, task: Task, event_type: str, message: str, details: Optional[Dict[str, Any]] = None):
        evt = TaskEvent(
            id=f"evt_{uuid.uuid4().hex[:8]}",
            task_id=task.id,
            event_type=event_type,
            message=message,
            details_json=json.dumps(details, default=str) if details else None,
            created_at=datetime.datetime.utcnow()
        )
        self.db.add(evt)
        self.db.commit()
        return evt

    def create_task(self, goal: str, scenario: str = "standard") -> Task:
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        task = Task(
            id=task_id,
            goal=goal,
            scenario=scenario,
            status=TaskStatus.PENDING,
            created_at=datetime.datetime.utcnow(),
            updated_at=datetime.datetime.utcnow()
        )
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)

        self._log_event(task, "INIT", f"CentrAlign Operator received business goal: '{goal}'", {"scenario": scenario})
        return task

    def cancel_task(self, task_id: str) -> Task:
        task = self.db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise ValueError(f"Task '{task_id}' not found.")
        task.status = TaskStatus.CANCELLED
        task.completed_at = datetime.datetime.utcnow()
        self._log_event(task, "STATE_CHANGE", "Task execution was cancelled by user request.")
        self.db.commit()
        self.db.refresh(task)
        return task

    def run_task(self, task_id: str) -> Task:
        task = self.db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise ValueError(f"Task '{task_id}' not found.")

        if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            return task

        # 1. State machine transition: PLANNING
        if not task.steps or task.status == TaskStatus.PENDING:
            task.status = TaskStatus.PLANNING
            self.db.commit()
            self._log_event(task, "PLANNING_START", "Analyzing business goal and synthesizing actionable plan.")

            plan_data = llm_provider.generate_plan(task.goal, tool_registry.get_catalog())
            for step_def in plan_data.get("steps", []):
                step = TaskStep(
                    id=f"step_{uuid.uuid4().hex[:8]}",
                    task_id=task.id,
                    step_order=step_def.get("step_order", 1),
                    description=step_def.get("description", ""),
                    tool_name=step_def.get("tool_name"),
                    status=StepStatus.PENDING,
                    created_at=datetime.datetime.utcnow()
                )
                self.db.add(step)
            self.db.commit()
            self._log_event(task, "PLAN_GENERATED", f"Generated structured {len(plan_data.get('steps', []))}-step plan.", plan_data)

        # 2. Execution Loop
        task.status = TaskStatus.RUNNING
        self.db.commit()

        browser_service = BrowserService(session_id=task.id)
        task_memory: Dict[str, Any] = {"scenario": task.scenario}

        # Reconstruct memory from prior completed tool executions across pauses/restarts
        for te in task.tool_executions:
            if te.status == "SUCCESS" and te.output_data_json:
                try:
                    out = json.loads(te.output_data_json)
                    self._update_task_memory(task_memory, te.tool_name, out)
                except Exception:
                    pass

        # Incorporate approved human clarifications into task_memory
        for appr in task.approvals:
            if appr.status == ApprovalStatus.APPROVED and appr.payload_json:
                try:
                    payload = json.loads(appr.payload_json)
                    if "due_date" in payload and "extracted_fields" in task_memory:
                        task_memory["extracted_fields"]["due_date"] = payload["due_date"]
                except Exception:
                    pass

        step_budget = settings.MAX_TOOL_CALLS_PER_TASK

        steps = self.db.query(TaskStep).filter(TaskStep.task_id == task.id).order_by(TaskStep.step_order).all()
        current_step_idx = 0

        # Find first non-completed step
        for idx, s in enumerate(steps):
            if s.status == StepStatus.COMPLETED:
                current_step_idx = idx + 1
            else:
                break

        while current_step_idx < len(steps) and step_budget > 0:
            step_budget -= 1
            current_step = steps[current_step_idx]
            current_step.status = StepStatus.RUNNING
            self.db.commit()

            # Context for tool execution
            context = {
                "db_session": self.db,
                "browser_service": browser_service,
                "task": task,
                "task_memory": task_memory,
                "scenario": task.scenario
            }

            # Planner selects next action
            action = llm_provider.select_next_action(
                goal=task.goal,
                plan=[{"step_order": s.step_order, "description": s.description, "tool_name": s.tool_name} for s in steps],
                current_step_index=current_step_idx,
                observations=[],
                task_memory=task_memory,
                available_tools=tool_registry.get_catalog()
            )

            tool_name = action.get("tool_name", current_step.tool_name)
            args = action.get("arguments", {})
            rationale = action.get("rationale", "")

            # Adapt arguments based on scenario
            if tool_name == "browser_search" and task.scenario == "recoverable_failure":
                args["scenario"] = "recoverable_failure"

            self._log_event(
                task,
                "ACTION_SELECTED",
                f"Step {current_step.step_order}: Planner selected '{tool_name}'",
                {"rationale": rationale, "arguments": args}
            )

            # Check Approval Policy Gate
            pending_appr = self.db.query(ApprovalRequest).filter(
                ApprovalRequest.task_id == task.id,
                ApprovalRequest.action_name == tool_name,
                ApprovalRequest.status == ApprovalStatus.PENDING
            ).first()

            if approval_manager.requires_approval(tool_name, args):
                # Check if approval already granted
                approved_record = self.db.query(ApprovalRequest).filter(
                    ApprovalRequest.task_id == task.id,
                    ApprovalRequest.action_name == tool_name,
                    ApprovalRequest.status == ApprovalStatus.APPROVED
                ).first()

                if not approved_record:
                    # Pause for human approval
                    appr = approval_manager.create_approval_request(
                        db=self.db,
                        task=task,
                        action_name=tool_name,
                        payload=args,
                        reason=f"Policy requires supervisor approval before creating financial records for {args.get('vendor', 'vendor')} (${args.get('total_amount', 0.0):,.2f})."
                    )
                    self._log_event(
                        task,
                        "APPROVAL_REQUESTED",
                        f"Execution paused. Consequential action '{tool_name}' requires human authorization.",
                        {"approval_id": appr.id, "payload": args}
                    )
                    return task
                else:
                    # Incorporate any clarification provided in approval
                    payload_data = json.loads(approved_record.payload_json)
                    args.update(payload_data)

            # Execute Tool with Retry & Recovery Logic
            retry_count = 0
            exec_result = None

            while True:
                exec_result = tool_executor.execute_tool(tool_name, args, context)
                
                # Persist tool execution
                tool_exec = ToolExecution(
                    id=f"texec_{uuid.uuid4().hex[:8]}",
                    task_id=task.id,
                    step_id=current_step.id,
                    tool_name=tool_name,
                    input_data_json=json.dumps(args),
                    output_data_json=json.dumps(exec_result.output, default=str),
                    duration_ms=exec_result.duration_ms,
                    status=exec_result.status,
                    error_message=exec_result.error_message,
                    retry_count=retry_count,
                    created_at=datetime.datetime.utcnow()
                )
                self.db.add(tool_exec)
                self.db.commit()

                if exec_result.status == "SUCCESS":
                    self._log_event(
                        task,
                        "TOOL_SUCCESS",
                        f"Tool '{tool_name}' completed in {exec_result.duration_ms}ms.",
                        exec_result.output
                    )
                    break

                # Check if duplicate creation was intentionally prevented
                if exec_result.output and exec_result.output.get("duplicate"):
                    self._log_event(
                        task,
                        "DUPLICATE_AVOIDED",
                        f"Invoice already exists in finance system. Duplicate creation avoided, proceeding to independent verification.",
                        exec_result.output
                    )
                    break

                # Error occurred: evaluate recovery
                recovery = recovery_manager.evaluate_failure(exec_result, retry_count)
                if recovery["action"] == "RETRY":
                    retry_count = recovery["retry_count"]
                    self._log_event(
                        task,
                        "RETRY_ATTEMPT",
                        recovery["reason"],
                        {"tool": tool_name, "attempt": retry_count}
                    )
                    time.sleep(recovery.get("delay_seconds", 0.5))
                    # On retry in recoverable_failure scenario, clear transient flag
                    if task.scenario == "recoverable_failure" and "scenario" in args:
                        args.pop("scenario", None)
                    continue
                else:
                    # Non-recoverable failure or retry exhausted
                    self._log_event(
                        task,
                        "UNRECOVERABLE_ERROR",
                        recovery["reason"],
                        {"error": exec_result.error_message}
                    )
                    current_step.status = StepStatus.FAILED
                    task.status = TaskStatus.FAILED
                    task.result_summary = f"Task failed at step {current_step.step_order} ({tool_name}): {exec_result.error_message}"
                    self.db.commit()
                    return task

            # Update Task Memory & State from Observations
            self._update_task_memory(task_memory, tool_name, exec_result.output)

            # Check if extracted invoice has ambiguous fields (Scenario C)
            if tool_name == "validate_invoice_fields":
                val_res = exec_result.output or {}
                if val_res.get("requires_clarification") or not val_res.get("valid"):
                    # Check if clarification approval already granted
                    approved_clarification = self.db.query(ApprovalRequest).filter(
                        ApprovalRequest.task_id == task.id,
                        ApprovalRequest.action_name == "clarify_ambiguous_due_date",
                        ApprovalRequest.status == ApprovalStatus.APPROVED
                    ).first()

                    if not approved_clarification:
                        # Pause for human clarification
                        appr = approval_manager.create_approval_request(
                            db=self.db,
                            task=task,
                            action_name="clarify_ambiguous_due_date",
                            payload=task_memory.get("extracted_fields", {}),
                            reason="Invoice has ambiguous or missing payment terms. Please provide the validated due date to continue."
                        )
                        task.status = TaskStatus.WAITING_FOR_INPUT
                        self._log_event(
                            task,
                            "INPUT_REQUESTED",
                            "Execution paused. Human clarification required for ambiguous due date.",
                            {"approval_id": appr.id}
                        )
                        self.db.commit()
                        return task
                    else:
                        # Human supervisor provided clarified due date!
                        clarified_payload = json.loads(approved_clarification.payload_json)
                        if "due_date" in clarified_payload:
                            task_memory["extracted_fields"]["due_date"] = clarified_payload["due_date"]
                            self._log_event(
                                task,
                                "CLARIFICATION_APPLIED",
                                f"Applied human-clarified due date: '{clarified_payload['due_date']}'."
                            )

            # Complete step
            current_step.status = StepStatus.COMPLETED
            current_step.completed_at = datetime.datetime.utcnow()
            self.db.commit()
            current_step_idx += 1

        # 3. Final Verification & Completion
        task.status = TaskStatus.VERIFYING
        self.db.commit()
        self._log_event(task, "VERIFICATION_START", "Running independent verification of destination records.")

        if "ticket" in task.goal.lower() or "internal task" in task.goal.lower():
            itask_id = task_memory.get("created_internal_task_id")
            ver_res = verification_engine.verify_internal_task(self.db, task.id, itask_id)
        else:
            fields = task_memory.get("extracted_fields", {})
            inv_num = fields.get("invoice_number", "ACM-2026-003")
            ver_res = verification_engine.verify_invoice(
                db=self.db,
                task_id=task.id,
                invoice_number=inv_num,
                expected_fields=fields,
                source_document_id=fields.get("source_document_id")
            )

        if ver_res.get("verified"):
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.datetime.utcnow()
            task.result_summary = (
                f"Successfully completed task. Invoice '{fields.get('invoice_number', 'ACM-2026-003')}' for "
                f"{fields.get('vendor', 'Acme Corp')} (${fields.get('total_amount', 0.0):,.2f}) extracted, "
                f"recorded, and independently verified with 100% field parity in finance database."
                if "ticket" not in task.goal.lower() else
                f"Successfully completed task. Internal task '{task_memory.get('created_internal_task_id')}' created from Acme Corp support ticket and verified in SQLite."
            )
            self._log_event(task, "TASK_COMPLETED", task.result_summary, ver_res)
        else:
            task.status = TaskStatus.FAILED
            task.result_summary = f"Task completed execution but independent verification failed: {ver_res.get('error', 'Discrepancy in records')}"
            self._log_event(task, "VERIFICATION_FAILED", task.result_summary, ver_res)

        self.db.commit()
        self.db.refresh(task)
        return task

    def _update_task_memory(self, memory: Dict[str, Any], tool_name: str, output: Optional[Dict[str, Any]]):
        if not output or not isinstance(output, dict):
            return

        if tool_name == "browser_extract_page":
            invoices = output.get("invoices", [])
            if invoices:
                # Select latest invoice by invoice_date
                sorted_invoices = sorted(invoices, key=lambda x: x.get("invoice_date", ""), reverse=True)
                latest = sorted_invoices[0]
                # If scenario is ambiguous_invoice, choose ambiguous invoice
                if memory.get("scenario") == "ambiguous_invoice":
                    for inv in invoices:
                        if "AMB" in inv.get("invoice_number", ""):
                            latest = inv
                            break
                memory["selected_invoice"] = latest
            if output.get("tickets"):
                memory["tickets"] = output.get("tickets")

        elif tool_name == "browser_download":
            memory["downloaded_doc_id"] = output.get("filename")

        elif tool_name == "extract_invoice_fields":
            memory["extracted_fields"] = output

        elif tool_name == "support_search_tickets":
            memory["tickets"] = output.get("tickets", [])

        elif tool_name == "support_create_internal_task":
            memory["created_internal_task_id"] = output.get("task_id")
