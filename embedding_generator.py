
from sentence_transformers import SentenceTransformer


# Load a pretrained model for generating text embeddings.
MODEL_NAME = "all-MiniLM-L6-v2"


model = SentenceTransformer(MODEL_NAME)


def generate_embeddings(chunks):
    """
    Convert a list of text chunks into numerical embeddings.
    """
    if not chunks:
        return []

    embeddings = model.encode(
        chunks,
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    return embeddings
