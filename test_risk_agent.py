
from risk_agent import detect_risks

sample_text = """
The project deadline may be missed.
We are waiting for dependency approval.
There is not enough time to test all modules.
The team completed the documentation.
"""

risks = detect_risks(sample_text)

if not risks:
    print("No risks detected.")
else:
    for risk in risks:
        print(f"\nCategory: {risk['category']}")
        print(f"Description: {risk['description']}")


assert detect_risks("") == []
assert detect_risks("   ") == []

print("Empty-input tests passed!")