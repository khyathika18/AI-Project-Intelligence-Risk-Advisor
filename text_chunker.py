
import re


def split_text(text, chunk_size=500, overlap=50):
    """
    Split text into readable chunks without cutting words
    or sentences unnecessarily.

    chunk_size: Maximum preferred number of characters.
    overlap: Approximate number of overlapping characters.
    """

    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive.")

    if overlap < 0 or overlap >= chunk_size:
        raise ValueError(
            "overlap must be non-negative and smaller than chunk_size."
        )

    if not isinstance(text, str):
        raise TypeError("Input text must be a string.")

    text = text.strip()

    if not text:
        return []

    # Normalize unnecessary whitespace.
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n+", "\n", text)

    # Split into sentences while preserving sentence-ending punctuation.
    sentences = re.split(
        r"(?<=[.!?])\s+|\n+",
        text
    )

    sentences = [
        sentence.strip()
        for sentence in sentences
        if sentence.strip()
    ]

    chunks = []
    current_chunk = ""

    for sentence in sentences:

        # Handle unusually long sentences.
        if len(sentence) > chunk_size:

            if current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = ""

            words = sentence.split()
            long_part = ""

            for word in words:

                if not long_part:
                    long_part = word

                elif len(long_part) + len(word) + 1 <= chunk_size:
                    long_part += " " + word

                else:
                    chunks.append(long_part.strip())
                    long_part = word

            if long_part:
                current_chunk = long_part

            continue

        # Add the sentence to the current chunk if it fits.
        if not current_chunk:

            current_chunk = sentence

        elif len(current_chunk) + len(sentence) + 1 <= chunk_size:

            current_chunk += " " + sentence

        else:

            chunks.append(current_chunk.strip())

            # Retain overlap from the previous chunk.
            if overlap > 0:

                previous_words = current_chunk.split()
                overlap_text = ""

                for word in reversed(previous_words):

                    candidate = (
                        word + " " + overlap_text
                    ).strip()

                    if len(candidate) <= overlap:
                        overlap_text = candidate

                    else:
                        break

                if overlap_text:
                    current_chunk = overlap_text + " " + sentence
                else:
                    current_chunk = sentence

            else:

                current_chunk = sentence

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks
