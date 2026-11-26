
from action_item_agent import identify_blockers_and_actions


# TEST 1: Original blocker without resolution evidence.
sample_text_1 = """
Testing is blocked because the test server is unavailable.
Action item: Prepare the test cases.
Assigned to Priya: Complete the database documentation.
The team completed the project introduction.
"""

result_1 = identify_blockers_and_actions(sample_text_1)

print("=" * 50)
print("TEST 1: ACTIVE BLOCKER")
print("=" * 50)

print("\nBLOCKERS:")
for item in result_1["blockers"]:
    print("-", item)

print("\nACTION ITEMS:")
for item in result_1["action_items"]:
    print("-", item)


# TEST 2: Later update confirms that the server is restored.
sample_text_2 = """
Testing is blocked because the test server is unavailable.
Action item: Contact infrastructure team and restore test server access.
The infrastructure team restored test server access.
The testing team resumed testing on 22 November 2026.
Ravi must complete the remaining test cases.
"""

result_2 = identify_blockers_and_actions(sample_text_2)

print("\n" + "=" * 50)
print("TEST 2: RESOLVED BLOCKER")
print("=" * 50)

print("\nACTIVE BLOCKERS:")
for item in result_2["blockers"]:
    print("-", item)

print("\nRESOLVED BLOCKERS:")
for item in result_2["resolved_blockers"]:
    print("-", item)

print("\nACTION ITEMS:")
for item in result_2["action_items"]:
    print("-", item)

print("\nBLOCKER STATUS:")
for item in result_2["blocker_status"]:
    print(item)
