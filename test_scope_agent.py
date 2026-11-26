from scope_agent import extract_scope

sample_text = """
Project Objective: Develop an AI-based student attendance system.
Project Objective: Develop a web-based system that allows faculty members to record student attendance and view attendance reports.

Project Deliverable: Submit the final project report.
Project Deliverable: Submit the working application, source code, and final project report.

Project Milestone: Complete testing by Week 4.
Project Milestone: Finish system testing by Week 5.

Assigned to Priya: Complete the database documentation.
Responsible for testing: Ravi.
"""

result = extract_scope(sample_text)

for category, statements in result.items():
    print(f"\n{category.upper()}:")
    for statement in statements:
        print("-", statement)