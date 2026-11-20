
import re


def extract_scope(text):
    result = {
        "goals": [],
        "deliverables": [],
        "milestones": [],
        "responsibilities": []
    }

    if not text or not text.strip():
        return result

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    patterns = {
        "goals": r"^(?:project\s+)?(?:goal|objective|aim)\s*:",
        "deliverables": (
            r"^(?:project\s+)?(?:deliverable|submission|"
            r"final report|prototype)\s*:"
        ),
        "milestones": (
            r"^(?:project\s+)?(?:milestone|deadline|due date|"
            r"timeline)\s*:"
        ),
        "responsibilities": (
            r"^(?:assigned to|responsible for|responsible|owner|"
            r"team member|project lead)\b.*:"
        )
    }

    for category, pattern in patterns.items():
        for line in lines:
            if re.search(pattern, line, re.IGNORECASE):
                result[category].append(line)

    return result
