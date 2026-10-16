
from embedding_generator import generate_embeddings


chunks = [
    "The project is delayed because a task is incomplete.",
    "An unfinished task may cause a schedule delay.",
    "The project budget has exceeded the approved amount."
]

embeddings = generate_embeddings(chunks)

print("Number of chunks:", len(chunks))
print("Embedding shape:", embeddings.shape)
print("Embeddings generated:", embeddings.shape[0] == len(chunks))

assert embeddings.shape[0] == len(chunks)
assert embeddings.shape[1] > 0

print("\nAll embedding tests passed!")
