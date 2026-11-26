
from conversational_agent import (
    build_knowledge_base,
    add_chunks_to_knowledge_base
)


def test_incremental_knowledge_base():

    original_chunks = [
        "The project develops a student attendance system.",
        "Faculty members can record student attendance."
    ]

    knowledge_base = build_knowledge_base(original_chunks)

    assert len(knowledge_base["chunks"]) == 2
    assert knowledge_base["index"].ntotal == 2

    new_chunks = [
        "The project develops a student attendance system.",
        "Testing will begin after development.",
        "The final report must be submitted."
    ]

    result = add_chunks_to_knowledge_base(
        knowledge_base,
        new_chunks
    )

    assert result["added"] == 2
    assert result["skipped"] == 1
    assert result["total_chunks"] == 4

    assert knowledge_base["index"].ntotal == 4

    print("Initial chunks: 2")
    print("New chunks added:", result["added"])
    print("Duplicate chunks skipped:", result["skipped"])
    print("Final chunks:", result["total_chunks"])

    print("INCREMENTAL KNOWLEDGE BASE TEST PASSED!")


if __name__ == "__main__":
    test_incremental_knowledge_base()
