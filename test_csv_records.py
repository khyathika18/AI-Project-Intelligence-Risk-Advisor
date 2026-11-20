
from document_loader import extract_csv_records

sample_csv = """Meeting Date,Owner,Action Item,Due Date,Status
2026-10-28,Priya,Complete database documentation,2026-10-30,Open
2026-10-28,Anil,Send project progress update,2026-10-29,Open
"""

records = extract_csv_records(
    "test.csv",
    sample_csv.encode("utf-8")
)

assert len(records) == 2
assert records[0]["Owner"] == "Priya"
assert records[0]["Action Item"] == "Complete database documentation"
assert records[1]["Owner"] == "Anil"

print("CSV record extraction tests passed!")
print(records)
