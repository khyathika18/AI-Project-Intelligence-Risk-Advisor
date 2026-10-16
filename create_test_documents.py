
from docx import Document
from reportlab.pdfgen import canvas

# Create a sample DOCX document
doc = Document()
doc.add_heading("Project Status Report", level=1)
doc.add_paragraph("Project deadline: 12 weeks")
doc.add_paragraph(
    "Risk: Payment module development is delayed."
)
doc.save("sample_report.docx")

# Create a sample PDF document
pdf = canvas.Canvas("sample_report.pdf")
pdf.drawString(72, 750, "Project Status Report")
pdf.drawString(72, 720, "Project deadline: 12 weeks")
pdf.drawString(
    72,
    690,
    "Risk: Payment module development is delayed."
)
pdf.save()

print("Created sample_report.docx")
print("Created sample_report.pdf")
