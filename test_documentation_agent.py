
from documentation_agent import generate_documentation

sample_scope = {
    "goals": [
        "Project objective: Develop an AI-based student attendance system.",
        "Project objective: Develop a web-based attendance system."
    ],
    "deliverables": [
        "Deliverable: Submit the final project report.",
        "Deliverable: Submit the working application and source code."
    ]
}

sample_risks = [
    {
        "category": "Schedule Risk",
        "description": "The project deadline may be missed."
    },
    {
        "category": "Testing Risk",
        "description": "There is not enough time to test all modules."
    },
    {
        "category": "Dependency Risk",
        "description": "Authentication API approval is pending."
    }
]

sample_actions = [
    "Assigned to Priya: Complete database documentation.",
    "Obtain API approval from the security team.",
    "Contact infrastructure team and restore test server access."
]

result = generate_documentation(
    sample_scope,
    sample_risks,
    sample_actions
)

print("\nUSER STORIES:")
print(len(result["user_stories"]))
for item in result["user_stories"]:
    print(item)

print("\nRISK REGISTER:")
print(len(result["risk_register"]))
for item in result["risk_register"]:
    print(item)

print("\nACTION ITEM REPORT:")
print(len(result["action_item_report"]))
for item in result["action_item_report"]:
    print(item)

assert len(result["user_stories"]) == 4
assert len(result["risk_register"]) == 3
assert len(result["action_item_report"]) == 3

print("\nALL DOCUMENTATION TESTS PASSED!")
