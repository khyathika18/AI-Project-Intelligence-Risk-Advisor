from action_item_agent import identify_blockers_and_actions
from risk_agent import detect_risks, reconcile_risks
from health_scoring import calculate_health_score

sample = """
Project Meeting Notes
Testing cannot continue because the test server is unavailable.
The team has not completed all test cases and may miss the sprint deadline.
There is not enough time to test all modules.
Additional Project Meeting Notes
The infrastructure team restored test server access.
The testing team resumed testing on 22 November 2026.
Ravi must complete the remaining test cases.
The project lead requested a testing progress update.
"""

result = identify_blockers_and_actions(sample)
assert result["blockers"] == [], result
assert len(result["resolved_blockers"]) == 1, result
assert result["blocker_status"][0]["status"] == "Resolved", result
assert any("remaining test cases" in item for item in result["action_items"]), result

risks = detect_risks(sample)
assert len(risks) >= 1, risks
risk_status = reconcile_risks(sample, risks)
assert all(item["status"] == "Active" for item in risk_status), risk_status

scope = {
    "goals": ["Build attendance system"],
    "deliverables": ["Working application"],
    "milestones": ["Testing by Week 4", "System testing by Week 5"],
}
health = calculate_health_score(scope, risk_status, result["blockers"])
assert health["blocker_count"] == 0, health
assert health["blocker_score"] == 30, health

print("Active blockers:", result["blockers"])
print("Resolved blockers:", result["resolved_blockers"])
print("Actions:", result["action_items"])
print("Risk statuses:", [item["status"] for item in risk_status])
print("Health result:", health)
print("STATUS TRACKING TEST PASSED")
