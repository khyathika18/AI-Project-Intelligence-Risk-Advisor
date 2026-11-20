
import re

from embedding_generator import generate_embeddings
from vector_store import build_vector_store, search_vector_store


# --------------------------------------------------
# 1. BUILD KNOWLEDGE BASE
# --------------------------------------------------

def build_knowledge_base(chunks):

    if not chunks:
        raise ValueError("No document chunks are available.")

    valid_chunks = [
        chunk.strip()
        for chunk in chunks
        if isinstance(chunk, str) and chunk.strip()
    ]

    if not valid_chunks:
        raise ValueError("No valid text chunks are available.")

    embeddings = generate_embeddings(valid_chunks)

    index = build_vector_store(embeddings)

    return {
        "chunks": valid_chunks,
        "index": index
    }


# --------------------------------------------------
# 2. RETRIEVE RELEVANT INFORMATION
# --------------------------------------------------

def ask_project_question(question, knowledge_base, top_k=3):

    if not question or not question.strip():
        raise ValueError("Please enter a question.")

    if not knowledge_base:
        raise ValueError("Knowledge base is not available.")

    query_embedding = generate_embeddings(
        [question.strip()]
    )[0]

    results = search_vector_store(
        knowledge_base["index"],
        query_embedding,
        knowledge_base["chunks"],
        top_k=top_k
    )

    return results


# --------------------------------------------------
# 3. CLEAN TEXT STATEMENTS
# --------------------------------------------------

def clean_statement(statement):

    statement = re.sub(
        r"^[\s\-•●▪*]+",
        "",
        statement
    )

    statement = re.sub(
        r"\s+",
        " ",
        statement
    )

    return statement.strip()


# --------------------------------------------------
# 4. EXTRACT INDIVIDUAL STATEMENTS
# --------------------------------------------------

def extract_statements(results):

    statements = []

    for result in results:

        chunk = result.get("chunk", "")

        # Separate bullet points and lines.
        parts = re.split(
            r"[\n•●▪]+",
            chunk
        )

        for part in parts:

            # Separate sentences.
            sentences = re.split(
                r"(?<=[.!?])\s+",
                part
            )

            for sentence in sentences:

                sentence = clean_statement(sentence)

                if len(sentence.split()) >= 4:
                    statements.append(sentence)

    return statements


# --------------------------------------------------
# 5. GET QUESTION KEYWORDS
# --------------------------------------------------

def get_question_keywords(question):

    stop_words = {
        "why", "what", "when", "where", "who",
        "how", "is", "are", "was", "were",
        "the", "a", "an", "of", "in", "on",
        "to", "for", "and", "or", "does",
        "do", "did", "can", "could", "would",
        "should", "about", "this", "that",
        "there", "their", "which", "with"
    }

    words = re.findall(
        r"\b[a-zA-Z]+\b",
        question.lower()
    )

    keywords = {
        word
        for word in words
        if word not in stop_words and len(word) > 2
    }

    # Related terms for better matching.
    related_terms = {

        "testing": [
            "test",
            "testing",
            "test cases"
        ],

        "delayed": [
            "delay",
            "delayed",
            "behind schedule"
        ],

        "delay": [
            "delay",
            "delayed",
            "behind schedule"
        ],

        "deadline": [
            "deadline",
            "due date",
            "submission"
        ],

        "server": [
            "server",
            "infrastructure",
            "unavailable"
        ],

        "blocked": [
            "blocked",
            "blocker",
            "unavailable"
        ],

        "risk": [
            "risk",
            "issue",
            "problem"
        ],

        "development": [
            "development",
            "application development"
        ],

        "blocker": [
            "blocker",
            "blocked",
            "unavailable"
        ],

        "issue": [
            "issue",
            "problem",
            "blocked"
        ]
    }

    expanded_keywords = set(keywords)

    for keyword in keywords:

        expanded_keywords.update(
            related_terms.get(keyword, [])
        )

    return expanded_keywords


# --------------------------------------------------
# 6. IDENTIFY MILESTONE STATEMENTS
# --------------------------------------------------

def is_milestone_statement(statement):

    text = statement.lower().strip()

    milestone_patterns = [

        r"^milestone\s*:",

        r"\bby week\s+\d+\b",

        r"\bcomplete testing by\b",

        r"\bfinish system testing by\b",

        r"\bsubmit the final project report by\b"
    ]

    return any(
        re.search(pattern, text)
        for pattern in milestone_patterns
    )


# --------------------------------------------------
# 7. IDENTIFY ACTION ITEM STATEMENTS
# --------------------------------------------------

def is_action_statement(statement):

    text = statement.lower().strip()

    # A milestone should not be treated as an action.
    if is_milestone_statement(text):
        return False

    action_patterns = [

        r"^action item\s*:",

        r"^follow up\b",

        r"^contact\b",

        r"^restore\b",

        r"^finish remaining\b",

        r"^complete the remaining\b",

        r"^prepare\b",

        r"^send\b",

        r"^obtain\b",

        r"^confirm\b",

        r"^assigned to\b"
    ]

    return any(
        re.search(pattern, text)
        for pattern in action_patterns
    )


# --------------------------------------------------
# 8. REMOVE SEMANTICALLY SIMILAR FINDINGS
# --------------------------------------------------

def are_similar_statements(statement1, statement2):

    stop_words = {
        "the", "a", "an", "is", "are",
        "was", "were", "to", "of", "in",
        "on", "and", "because", "that",
        "this", "cannot", "not", "may",
        "has", "have", "been"
    }

    words1 = set(
        re.findall(r"\b[a-zA-Z]+\b", statement1.lower())
    ) - stop_words

    words2 = set(
        re.findall(r"\b[a-zA-Z]+\b", statement2.lower())
    ) - stop_words

    if not words1 or not words2:
        return False

    common_words = words1.intersection(words2)

    similarity = len(common_words) / min(
        len(words1),
        len(words2)
    )

    return similarity >= 0.65


def remove_duplicate_statements(statements):

    unique_statements = []

    for statement in statements:

        duplicate = False

        for existing in unique_statements:

            if are_similar_statements(
                statement,
                existing
            ):

                duplicate = True
                break

        if not duplicate:
            unique_statements.append(statement)

    return unique_statements


# --------------------------------------------------
# 9. GENERATE PROJECT ANSWER
# --------------------------------------------------

def generate_project_answer(question, results):

    if not results:

        return {
            "answer": (
                "No relevant information was found "
                "in the uploaded documents."
            ),
            "key_findings": [],
            "suggested_actions": []
        }

    statements = extract_statements(results)

    keywords = get_question_keywords(question)

    # ----------------------------------------------
    # Identify relevant statements
    # ----------------------------------------------

    scored_findings = []

    for statement in statements:

        statement = clean_statement(statement)

        if len(statement.split()) < 5:
            continue

        statement_lower = statement.lower()

        score = sum(
            1
            for keyword in keywords
            if keyword in statement_lower
        )

        if score > 0:

            scored_findings.append(
                (score, statement)
            )

    # Sort by relevance.
    scored_findings.sort(
        key=lambda item: item[0],
        reverse=True
    )

    # ----------------------------------------------
    # Separate findings and action items
    # ----------------------------------------------

    candidate_findings = []

    for score, statement in scored_findings:

        # Exclude milestones.
        if is_milestone_statement(statement):
            continue

        # Exclude action items.
        if is_action_statement(statement):
            continue

        candidate_findings.append(statement)

    # Remove duplicate or highly similar findings.
    key_findings = remove_duplicate_statements(
        candidate_findings
    )

    key_findings = key_findings[:4]

    # ----------------------------------------------
    # Identify related action items
    # ----------------------------------------------

    suggested_actions = []

    seen_actions = set()

    action_keywords = set(keywords)

    # Use findings to identify relevant actions.
    findings_text = " ".join(
        key_findings
    ).lower()

    if "server" in findings_text:

        action_keywords.update([
            "server",
            "infrastructure",
            "contact",
            "restore"
        ])

    if "testing" in findings_text or "test cases" in findings_text:

        action_keywords.update([
            "testing",
            "test",
            "test cases",
            "finish",
            "complete"
        ])

    for statement in statements:

        statement = clean_statement(statement)

        if not is_action_statement(statement):
            continue

        statement_lower = statement.lower()

        is_relevant = any(
            keyword in statement_lower
            for keyword in action_keywords
        )

        if is_relevant:

            normalized = statement_lower.strip()

            if normalized not in seen_actions:

                seen_actions.add(normalized)

                suggested_actions.append(statement)

        if len(suggested_actions) >= 3:
            break

    # Remove highly similar action items.
    suggested_actions = remove_duplicate_statements(
        suggested_actions
    )

    # ----------------------------------------------
    # Prepare final answer
    # ----------------------------------------------

    if key_findings:

        answer = (
            "The project documents indicate that "
            "the issue is related to the following factors:"
        )

    else:

        answer = (
            "The uploaded documents contain some related "
            "information, but there is not enough evidence "
            "to provide a clear answer."
        )

    return {

        "answer": answer,

        "key_findings": key_findings,

        "suggested_actions": suggested_actions[:3]

    }
