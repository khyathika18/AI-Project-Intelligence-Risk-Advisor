
from embedding_generator import generate_embeddings
from vector_store import build_vector_store, search_vector_store


chunks = [
    "The project is delayed because software testing is incomplete.",
    "The database migration is blocked by unresolved technical issues.",
    "The project budget has exceeded the approved amount."
]

# Generate embeddings for the document chunks.
embeddings = generate_embeddings(chunks)

# Build the FAISS index.
index = build_vector_store(embeddings)

# Convert the user's question into an embedding.
question = "Why is the project schedule delayed?"
query_embedding = generate_embeddings([question])[0]

# Retrieve the most relevant chunks.
results = search_vector_store(
    index,
    query_embedding,
    chunks,
    top_k=2
)

print("Number of indexed chunks:", index.ntotal)
print("\nSearch results:")

for result in results:
    print(f"Score: {result['score']:.4f}")
    print(f"Chunk: {result['chunk']}\n")

assert index.ntotal == len(chunks)
assert len(results) == 2
assert "delayed" in results[0]["chunk"].lower()

print("All vector store tests passed!")
