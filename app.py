
import streamlit as st

from document_loader import extract_text
from text_chunker import split_text


st.set_page_config(
    page_title="AI Project Intelligence & Risk Advisor",
    page_icon="📄",
    layout="wide"
)

st.title("AI Project Intelligence & Risk Advisor")
st.write(
    "Upload multiple project documents and generate text chunks "
    "for further analysis."
)

uploaded_files = st.file_uploader(
    "Upload project documents",
    type=["pdf", "docx", "csv", "txt"],
    accept_multiple_files=True
)

chunk_size = st.number_input(
    "Chunk size (characters)",
    min_value=100,
    max_value=2000,
    value=500,
    step=100
)

overlap = st.number_input(
    "Chunk overlap (characters)",
    min_value=0,
    max_value=int(chunk_size) - 1,
    value=min(50, int(chunk_size) - 1),
    step=10
)

if st.button("Process Documents", type="primary"):
    if not uploaded_files:
        st.warning("Please upload at least one document.")
    else:
        all_chunks = []
        file_errors = []

        progress = st.progress(0)

        for i, uploaded_file in enumerate(uploaded_files):
            try:
                file_bytes = uploaded_file.getvalue()

                text = extract_text(
                    uploaded_file.name,
                    file_bytes
                )

                chunks = split_text(
                    text,
                    chunk_size=int(chunk_size),
                    overlap=int(overlap)
                )

                for chunk_number, chunk in enumerate(chunks, start=1):
                    all_chunks.append({
                        "file_name": uploaded_file.name,
                        "chunk_number": chunk_number,
                        "text": chunk
                    })

            except Exception as error:
                file_errors.append(
                    f"{uploaded_file.name}: {error}"
                )

            progress.progress((i + 1) / len(uploaded_files))

        st.session_state["document_chunks"] = all_chunks

        st.success(
            f"Processing finished: {len(uploaded_files)} files selected, "
            f"{len(all_chunks)} chunks generated."
        )

        for error in file_errors:
            st.error(error)

if "document_chunks" in st.session_state:
    chunks = st.session_state["document_chunks"]

    st.subheader("Processing Summary")

    col1, col2 = st.columns(2)
    col1.metric("Chunks generated", len(chunks))
    col2.metric(
        "Files represented",
        len(set(chunk["file_name"] for chunk in chunks))
    )

    st.subheader("Generated Text Chunks")

    if chunks:
        for chunk in chunks:
            with st.expander(
                f"{chunk['file_name']} — Chunk {chunk['chunk_number']}"
            ):
                st.write(chunk["text"])
                st.caption(
                    f"Characters: {len(chunk['text'])}"
                )
    else:
        st.info("No chunks were generated from the selected documents.")
