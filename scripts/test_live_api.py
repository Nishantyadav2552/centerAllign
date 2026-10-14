import httpx
import time

def test_live_workflow():
    client = httpx.Client(base_url="http://127.0.0.1:8000")
    
    # 1. Create task
    print("Creating autonomous task...")
    res = client.post(
        "/api/tasks",
        json={
            "goal": "Find the latest invoice from Acme Corp, extract fields, enter into finance, and verify.",
            "scenario": "standard"
        }
    )
    task = res.json()
    task_id = task["id"]
    print(f"Task created: {task_id} (Status: {task['status']})")

    # 2. Wait for it to hit the approval gate
    for _ in range(10):
        time.sleep(0.5)
        task_data = client.get(f"/api/tasks/{task_id}").json()
        status = task_data["status"]
        if status in ["WAITING_FOR_APPROVAL", "COMPLETED", "FAILED"]:
            break
    print(f"Task reached status: {status}")

    # 3. Check approvals
    approvals = client.get(f"/api/tasks/{task_id}/approvals").json()
    if approvals:
        pending = [a for a in approvals if a["status"] == "PENDING"]
        if pending:
            print(f"Found pending approval: {pending[0]['id']} for action '{pending[0]['action_name']}'")
            print("Granting human supervisor authorization...")
            client.post(
                f"/api/approvals/{pending[0]['id']}/decision",
                json={"decision": "APPROVED", "decision_by": "Recruiting Reviewer"}
            )

    # 4. Wait for completion
    for _ in range(15):
        time.sleep(0.5)
        task_data = client.get(f"/api/tasks/{task_id}").json()
        status = task_data["status"]
        if status in ["COMPLETED", "FAILED"]:
            break

    print(f"Final Task Status: {status}")
    print(f"Result Summary: {task_data.get('result_summary')}")

    # 5. Get report
    report = client.get(f"/api/tasks/{task_id}/report").json()
    print(f"Steps Completed: {report['steps_completed']}/{report['steps_count']}")
    print(f"Verifications Count: {len(report['verifications'])}")
    if report["verifications"]:
        print(f"Verified: {report['verifications'][0]['verified']}")

if __name__ == "__main__":
    test_live_workflow()
