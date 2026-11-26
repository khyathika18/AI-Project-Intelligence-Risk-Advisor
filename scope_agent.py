
import re


def clean_line(line):
    """Normalize whitespace and remove common bullet markers."""
    line = line.strip()
    line = re.sub(r"^[•*\-]+\s*", "", line)
    line = re.sub(r"\s+", " ", line)
    return line.strip()


def normalize_text(text):
    """Create a comparable version of a statement."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def get_keywords(statement):
    """Extract meaningful keywords from a scope statement."""
    normalized = normalize_text(statement)

    normalized = re.sub(
        r"^(project\s+)?(objective|goal|aim|deliverable|"
        r"submission|final report|prototype)\s+",
        "",
        normalized
    )

    stop_words = {
        "the", "a", "an", "to", "of", "and", "for",
        "in", "on", "by", "with", "is", "are",
        "that", "this", "it", "as", "from"
    }

    return {
        word for word in normalized.split()
        if word not in stop_words
    }


def remove_overlapping_statements(statements):
    """
    Remove exact duplicates and less informative statements
    when a more detailed statement covers most of their keywords.
    """
    unique_statements = []

    for statement in statements:
        statement = clean_line(statement)

        if not statement:
            continue

        normalized = normalize_text(statement)

        if not any(
            normalize_text(existing) == normalized
            for existing in unique_statements
        ):
            unique_statements.append(statement)

    filtered_statements = []

    for statement in unique_statements:
        current_words = get_keywords(statement)

        if not current_words:
            filtered_statements.append(statement)
            continue

        less_informative = False

        for other in unique_statements:
            if statement == other:
                continue

            other_words = get_keywords(other)

            if len(other_words) <= len(current_words):
                continue

            overlap = len(current_words & other_words)
            overlap_ratio = overlap / len(current_words)

            if overlap_ratio >= 0.60:
                less_informative = True
                break

        if not less_informative:
            filtered_statements.append(statement)

    return filtered_statements


def extract_scope(text):
    """
    Extract project goals, deliverables, milestones,
    and responsibilities from project documents.
    """

    result = {
        "goals": [],
        "deliverables": [],
        "milestones": [],
        "responsibilities": []
    }

    if not text or not text.strip():
        return result

    lines = [
        clean_line(line)
        for line in text.splitlines()
        if line.strip()
    ]

    patterns = {
        "goals": (
            r"^(?:project\s+)?"
            r"(?:goal|objective|aim)\s*:"
        ),
        "deliverables": (
            r"^(?:project\s+)?"
            r"(?:deliverable|submission|"
            r"final report|prototype)\s*:"
        ),
        "milestones": (
            r"^(?:project\s+)?"
            r"(?:milestone|deadline|due date|"
            r"timeline)\s*:"
        ),
        "responsibilities": (
            r"^(?:assigned to|responsible for|responsible|"
            r"owner|team member|project lead)\b.*:"
        )
    }

    # Extract statements by category.
    for line in lines:
        for category, pattern in patterns.items():
            if re.search(pattern, line, re.IGNORECASE):
                result[category].append(line)
                break

    # Consolidate duplicate and overlapping goals.
    result["goals"] = remove_overlapping_statements(
        result["goals"]
    )

    # Consolidate duplicate and overlapping deliverables.
    result["deliverables"] = remove_overlapping_statements(
        result["deliverables"]
    )

    # Preserve all milestones, including conflicting ones.
    # Downstream analysis needs both dates to detect conflicts.

    # Remove duplicate or overlapping responsibilities.
    result["responsibilities"] = remove_overlapping_statements(
        result["responsibilities"]
    )

    return result
