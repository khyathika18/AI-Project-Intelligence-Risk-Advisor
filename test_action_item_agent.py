
from action_item_agent import identify_blockers_and_actions

sample_text = """
Testing is blocked because the test server is unavailable.
Action item: Prepare the test cases.
Assigned to Priya: Complete the database documentation.
The team completed the project introduction.
"""

result = identify_blockers_and_actions(sample_text)

print("BLOCKERS:")
for item in result["blockers"]:
    print("-", item)

print("\nACTION ITEMS:")
for item in result["action_items"]:
    print("-", item)
