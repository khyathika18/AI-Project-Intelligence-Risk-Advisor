
from document_loader import extract_text
from text_chunker import split_text
from embedding_generator import generate_embeddings
from vector_store import build_vector_store, search_vector_store


def process_document(file_name, file_bytes):
    """
    Extract, chunk, embed, and index an uploaded document.
    """
    # 1. Extract text from the uploaded document.
    text = extract_text(file_name, file_bytes)

    # 2. Split the text into smaller chunks.
    chunks = split_text(text)

    if not chunks:
        raise ValueError("No text chunks were generated.")

    # 3. Convert chunks into numerical embeddings.
    embeddings = generate_embeddings(chunks)

    # 4. Build the FAISS vector index.
    index = build_vector_store(embeddings)

    return {
        "file_name": file_name,
        "chunks": chunks,
        "index": index
    }


def ask_question(question, document_data, top_k=3):
    """
    Retrieve relevant document chunks for a user's question.
    """
    if not question or not question.strip():
        raise ValueError("Question cannot be empty.")

    chunks = document_data["chunks"]
    index = document_data["index"]

    # Embed the user's question.
    query_embedding = generate_embeddings([question.strip()])[0]

    # Retrieve the most relevant chunks.
    results = search_vector_store(
        index,
        query_embedding,
        chunks,
        top_k=top_k
    )

    return results
