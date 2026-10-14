import time
import json
import sys
from pathlib import Path
from sqlalchemy.orm import Session

# Add repo root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.db.session import engine, Base, SessionLocal
from backend.app.models import Task, TaskStep, TaskEvent, ToolExecution, InvoiceRecord, ApprovalRequest, TaskStatus
from backend.app.core.orchestrator import TaskOrchestrator
from backend.app.core.approvals import approval_manager
from backend.app.core.config import settings

def run_evaluation_suite():
    print("=" * 70)
    print("CentrAlign Operator • Autonomous Agent Evaluation Suite")
    print("=" * 70)
    print(f"Mode: {'DETERMINISTIC DEMO' if settings.DEMO_MODE else 'LLM DRIVEN'}")
    print(f"Max tool calls per task: {settings.MAX_TOOL_CALLS_PER_TASK}")
    print(f"Max retries per action: {settings.MAX_RETRIES_PER_ACTION}")
    print("-" * 70)

    # Initialize clean DB tables for evaluation
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    eval_scenarios = [
        {
            "name": "Scenario A: Standard End-to-End Invoice Processing",
            "goal": "Find the latest invoice from Acme Corp, extract the invoice number, invoice date, total amount, and due date, enter the information into our finance system, and verify that it was saved correctly.",
            "scenario": "standard",
            "auto_approve": True
        },
        {
            "name": "Scenario B: Recoverable Transient Failure & Self-Healing",
            "goal": "Find the latest invoice from Acme Corp, extract fields, record in finance system, and verify.",
            "scenario": "recoverable_failure",
            "auto_approve": True
        },
        {
            "name": "Scenario C: Ambiguous Due Date & Human Clarification",
            "goal": "Find the latest invoice from Acme Corp, extract the invoice number, invoice date, total amount, and due date, enter the information into our finance system, and verify that it was saved correctly.",
            "scenario": "ambiguous_invoice",
            "auto_approve": True,
            "clarify_input": "2026-11-15"
        },
        {
            "name": "Scenario D: Duplicate Invoice Prevention",
            "goal": "Find the latest invoice from Acme Corp and enter into finance system.",
            "scenario": "standard",
            "expect_duplicate": True,
            "auto_approve": True
        },
        {
            "name": "Scenario E: Generalization (Support Ticket to Internal Task)",
            "goal": "Find the latest support ticket from customer Acme Corp, summarize the issue, create an internal follow-up task, and verify that the task exists.",
            "scenario": "generalization",
            "auto_approve": True
        }
    ]

    total_tasks = len(eval_scenarios)
    tasks_passed = 0
    verifications_passed = 0
    recovery_attempts = 0
    recovery_successes = 0
    duplicate_writes_blocked = 0
    total_tool_calls = 0
    total_duration_sec = 0.0
    failure_categories = {}

    start_eval_time = time.perf_counter()

    for sc in eval_scenarios:
        print(f"\n[RUNNING] {sc['name']}...")
        orch = TaskOrchestrator(db)
        t_start = time.perf_counter()
        
        task = orch.create_task(goal=sc["goal"], scenario=sc["scenario"])
        
        # First execution run
        orch.run_task(task.id)

        if task.status == TaskStatus.WAITING_FOR_INPUT and sc.get("clarify_input"):
            appr = db.query(ApprovalRequest).filter(
                ApprovalRequest.task_id == task.id,
                ApprovalRequest.status == "PENDING"
            ).first()
            if appr:
                print(f"  -> Ambiguous field detected. Providing clarified due date '{sc['clarify_input']}'...")
                approval_manager.handle_decision(
                    db,
                    appr.id,
                    "APPROVED",
                    decision_by="Supervisor Evaluator",
                    clarification_value=sc["clarify_input"]
                )
                orch.run_task(task.id)

        # Handle financial creation approval if paused
        if task.status == TaskStatus.WAITING_FOR_APPROVAL and sc.get("auto_approve", True):
            appr = db.query(ApprovalRequest).filter(
                ApprovalRequest.task_id == task.id,
                ApprovalRequest.status == "PENDING"
            ).first()
            if appr:
                print(f"  -> Consequential action gate triggered for {appr.action_name}. Auto-approving...")
                approval_manager.handle_decision(db, appr.id, "APPROVED", decision_by="Evaluation Runner")
                orch.run_task(task.id)

        duration = time.perf_counter() - t_start
        total_duration_sec += duration

        # Count tool calls
        execs = db.query(ToolExecution).filter(ToolExecution.task_id == task.id).all()
        total_tool_calls += len(execs)

        # Check retries & recovery
        retries = [e for e in execs if e.retry_count > 0]
        if retries:
            recovery_attempts += 1
            if task.status == TaskStatus.COMPLETED:
                recovery_successes += 1

        # Check duplicate block
        if sc.get("expect_duplicate"):
            dup_exec = [e for e in execs if "already exists" in str(e.output_data_json).lower()]
            if dup_exec:
                duplicate_writes_blocked += 1
                print("  -> Duplicate write was successfully detected and blocked.")

        # Verification check
        ver_count = len(task.verifications)
        ver_ok = all(v.verified for v in task.verifications) if ver_count > 0 else False
        if ver_ok:
            verifications_passed += 1

        if task.status == TaskStatus.COMPLETED:
            tasks_passed += 1
            print(f"  [SUCCESS] Completed in {duration:.2f}s ({len(execs)} tool calls). Verification: {'PASS' if ver_ok else 'N/A'}")
        else:
            cat = task.status.value
            failure_categories[cat] = failure_categories.get(cat, 0) + 1
            print(f"  [PARTIAL/FAILED] Status: {task.status.value}. Summary: {task.result_summary}")

    db.close()
    elapsed = time.perf_counter() - start_eval_time

    print("\n" + "=" * 70)
    print("EVALUATION METRICS REPORT")
    print("=" * 70)
    print(f"Total Scenarios Evaluated: {total_tasks}")
    print(f"Task Success Rate:         {tasks_passed / total_tasks * 100:.1f}% ({tasks_passed}/{total_tasks})")
    print(f"Verification Pass Rate:    {verifications_passed / total_tasks * 100:.1f}% ({verifications_passed}/{total_tasks})")
    print(f"Recovery Success Rate:      {100.0 if recovery_attempts == 0 else (recovery_successes / recovery_attempts * 100):.1f}% ({recovery_successes}/{max(1, recovery_attempts)})")
    print(f"Duplicate Writes Prevented:{duplicate_writes_blocked}")
    print(f"Average Tool Calls/Task:   {total_tool_calls / max(1, total_tasks):.1f}")
    print(f"Total Evaluation Time:     {elapsed:.2f}s (Avg {elapsed/total_tasks:.2f}s/scenario)")
    print(f"Failure Categories:        {failure_categories if failure_categories else 'None (0 failures)'}")
    print("-" * 70)
    print("NOTE: These metrics are measured deterministically against controlled sandbox scenarios.")
    print("=" * 70)

if __name__ == "__main__":
    run_evaluation_suite()
