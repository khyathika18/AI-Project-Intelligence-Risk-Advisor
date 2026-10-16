
from pathlib import Path
from document_pipeline import process_document, ask_question


# Use an existing sample PDF from the project folder.
pdf_path = Path(__file__).parent / "sample_report.pdf"

with open(pdf_path, "rb") as file:
    file_bytes = file.read()

document_data = process_document(
    pdf_path.name,
    file_bytes
)

print("Document:", document_data["file_name"])
print("Number of chunks:", len(document_data["chunks"]))
print("Indexed vectors:", document_data["index"].ntotal)

question = "What risks or delays are mentioned in the project?"

results = ask_question(
    question,
    document_data,
    top_k=3
)

print("\nRetrieved results:")

for result in results:
    print(f"\nScore: {result['score']:.4f}")
    print(result["chunk"])

assert len(document_data["chunks"]) > 0
assert document_data["index"].ntotal == len(document_data["chunks"])
assert len(results) > 0

print("\nAll document pipeline tests passed!")
