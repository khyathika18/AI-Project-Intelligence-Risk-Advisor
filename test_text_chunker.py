
from text_chunker import split_text

text = "A" * 1200

chunks = split_text(
    text,
    chunk_size=500,
    overlap=50
)

print("Number of chunks:", len(chunks))
print("Chunk lengths:", [len(chunk) for chunk in chunks])

assert len(chunks) == 3
assert len(chunks[0]) == 500
assert len(chunks[1]) == 500
assert len(chunks[2]) == 300

assert chunks[0][-50:] == chunks[1][:50]
assert chunks[1][-50:] == chunks[2][:50]

assert split_text("") == []

print("\nAll text chunking tests passed!")
