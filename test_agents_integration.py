
from scope_agent import extract_scope
from risk_agent import detect_risks
from action_item_agent import identify_blockers_and_actions


sample_text = """
Project objective: Develop an AI-based student attendance system.
Deliverable: Submit the final project report.
Milestone: Complete testing by Week 4.
Responsible for testing: Ravi.

The project deadline may be missed.
We are waiting for dependency approval.
There is not enough time to test all modules.

Testing is blocked because the test server is unavailable.
Action item: Prepare the test cases.
Assigned to Priya: Complete the database documentation.
"""


# Test scope extraction
scope = extract_scope(sample_text)

assert scope["goals"], "Goal was not detected"
assert scope["deliverables"], "Deliverable was not detected"
assert scope["milestones"], "Milestone was not detected"
assert scope["responsibilities"], "Responsibility was not detected"

# Test risk detection
risks = detect_risks(sample_text)
risk_categories = {risk["category"] for risk in risks}

assert "Schedule Risk" in risk_categories
assert "Dependency Risk" in risk_categories
assert "Testing Risk" in risk_categories

# Test blockers and action items
actions = identify_blockers_and_actions(sample_text)

assert actions["blockers"], "Blocker was not detected"
assert len(actions["action_items"]) >= 2, (
    "Expected at least two action items"
)

print("Scope extraction tests passed!")
print("Risk detection tests passed!")
print("Blocker and action item tests passed!")
print("All integration tests passed!")
