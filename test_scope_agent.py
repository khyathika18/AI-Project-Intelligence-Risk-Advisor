
from scope_agent import extract_scope

sample_text = """
Project objective: Build a student attendance system.
Deliverable: Submit the final project report.
Milestone: Complete testing by Week 4.
Responsible for testing: Ravi.
"""

result = extract_scope(sample_text)

for category, items in result.items():
    print(f"\n{category.upper()}:")
    if items:
        for item in items:
            print("-", item)
    else:
        print("- None found")
