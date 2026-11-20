
from io import BytesIO, StringIO

import pandas as pd
from docx import Document
from pypdf import PdfReader


def extract_text(file_name, file_bytes):
    """
    Extract readable text from PDF, DOCX, CSV, or TXT files.
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


def extract_csv_records(file_name, file_bytes):
    """
    Extract CSV data as a list of dictionaries,
    with one dictionary per row.
    """

    extension = file_name.lower().rsplit(".", 1)[-1]

    if extension != "csv":
        raise ValueError(
            "This function only supports CSV files."
        )

    dataframe = pd.read_csv(
        StringIO(file_bytes.decode("utf-8-sig"))
    )

    dataframe.columns = dataframe.columns.str.strip()
    dataframe = dataframe.fillna("")

    return dataframe.to_dict(orient="records")
