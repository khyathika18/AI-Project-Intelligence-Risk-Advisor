
from text_chunker import split_text


sample_text = """
The project objective is to develop an AI-based student attendance system.
The team has not completed all test cases and may miss the sprint deadline.
Testing cannot continue because the test server is unavailable.
The infrastructure team must restore server access.
The final project report must be submitted.
"""

chunks = split_text(
    sample_text,
    chunk_size=100,
    overlap=20
)

print("\nGENERATED CHUNKS\n")

for number, chunk in enumerate(chunks, start=1):

    print(f"Chunk {number}:")
    print(chunk)
    print("-" * 50)

assert all(chunk.strip() for chunk in chunks)

print("\nCHUNKING TEST PASSED!")
