
from io import BytesIO, StringIO

import pandas as pd
from docx import Document
from pypdf import PdfReader


def extract_text(file_name, file_bytes):
    """
    Extract readable text from PDF, DOCX, CSV, or TXT files.

    Args:
        file_name: Original name of the uploaded file.
        file_bytes: Contents of the file as bytes.

    Returns:
        Extracted text as a string.
    """

    extension = file_name.lower().rsplit(".", 1)[-1]

    if extension == "pdf":
        reader = PdfReader(BytesIO(file_bytes))
        text = "\n".join(
            page.extract_text() or ""
            for page in reader.pages
        )

    elif extension == "docx":
        document = Document(BytesIO(file_bytes))
        text = "\n".join(
            paragraph.text
            for paragraph in document.paragraphs
        )

    elif extension == "csv":
        dataframe = pd.read_csv(
            StringIO(file_bytes.decode("utf-8-sig"))
        )
        text = dataframe.to_string(index=False)

    elif extension == "txt":
        text = file_bytes.decode("utf-8-sig")

    else:
        raise ValueError(
            f"Unsupported file type: .{extension}"
        )

    text = text.strip()

    if not text:
        raise ValueError(
            f"No readable text found in {file_name}"
        )

    return text
