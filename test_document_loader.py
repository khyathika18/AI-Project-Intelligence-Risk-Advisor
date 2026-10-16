
from document_loader import extract_text

# Test 1: TXT extraction
txt_content = """
Project: AI Project Intelligence & Risk Advisor
Deadline: 12 weeks
Blocker: Payment module development is delayed.
"""

txt_result = extract_text(
    "project_update.txt",
    txt_content.encode("utf-8")
)

assert "12 weeks" in txt_result
assert "Payment module" in txt_result
print("TXT test passed!")


# Test 2: CSV extraction
csv_content = """Task,Owner,Status
Requirement Analysis,Asha,Completed
Payment Module,Ravi,Delayed
Testing,Meena,Pending
"""

csv_result = extract_text(
    "sample_tasks.csv",
    csv_content.encode("utf-8")
)

assert "Payment Module" in csv_result
assert "Delayed" in csv_result
print("CSV test passed!")


# Test 3: DOCX extraction
with open("sample_report.docx", "rb") as file:
    docx_bytes = file.read()

docx_result = extract_text(
    "sample_report.docx",
    docx_bytes
)

assert "12 weeks" in docx_result
assert "Payment module" in docx_result
print("DOCX test passed!")


# Test 4: PDF extraction
with open("sample_report.pdf", "rb") as file:
    pdf_bytes = file.read()

pdf_result = extract_text(
    "sample_report.pdf",
    pdf_bytes
)

assert "12 weeks" in pdf_result
assert "Payment module" in pdf_result
print("PDF test passed!")


print("\nAll four document extraction tests passed!")

