
import re


RISK_PATTERNS = {
    "Schedule Risk": [
        r"\bmay be delayed\b",
        r"\bmight be delayed\b",
        r"\bat risk of delay\b",
        r"\bbehind schedule\b",
        r"\bbehind the schedule\b",
        r"\bdeadline is at risk\b",
        r"\binsufficient time to complete\b",
        r"\bdeadline may be missed\b",
        r"\bmay miss (?:the )?(?:sprint )?deadline\b",
        r"\bdeadline.*(?:at risk|missed|delay)\b",
        r"\bproject may not finish on time\b",
        r"\bdevelopment is behind schedule\b",
    ],

    "Testing Risk": [
        r"\binsufficient time for testing\b",
        r"\bnot enough time to test\b",
        r"\btesting may be delayed\b",
        r"\btesting is at risk\b",
        r"\btesting deadline may be missed\b",
        r"\bthere is not enough time to test\b",
        r"\bmay not complete testing\b",
        r"\binsufficient time to test\b",
    ],

    "Dependency Risk": [
        r"\bproject depends on\b.{0,100}\b(?:may be delayed|might be delayed|at risk)\b",
        r"\bexternal dependency may delay\b",
        r"\bdependency delay may affect\b",
        r"\bdependency may affect the deadline\b",
    ],

    "Resource Risk": [
        r"\binsufficient resources\b",
        r"\bresource shortage\b",
        r"\bnot enough staff\b",
        r"\bteam member unavailable\b",
        r"\black of resources\b",
        r"\bresource constraints may\b",
    ],
}


def normalize_text(text):
    """Normalize whitespace."""
    return re.sub(r"\s+", " ", str(text or "")).strip()


def clean_risk_line(line):
    """
    Remove bullet symbols, numbering and discussion labels
    before analyzing a line.
    """

    line = normalize_text(line)

    # Remove leading bullet symbols.
    line = re.sub(r"^[•●▪◦*-]+\s*", "", line)

    # Remove numbering such as 1. or 2)
    line = re.sub(r"^\d+[.)]\s*", "", line)

    # Remove Discussion label but preserve its content.
    line = re.sub(
        r"^Discussion\s*:\s*",
        "",
        line,
        flags=re.IGNORECASE
    )

    return normalize_text(line)


def is_non_risk_entry(line):
    """
    Exclude issue labels, action items, blockers,
    decisions and other non-risk entries.
    """

    text = normalize_text(line).casefold()

    excluded_prefixes = (
        "issue:",
        "action item:",
        "blocker:",
        "decision:",
        "todo:",
    )

    return text.startswith(excluded_prefixes)


def is_heading_only(raw_line, cleaned_line):
    """
    Exclude numbered headings such as:
    3. Testing behind schedule

    Preserve complete risk statements.
    """

    has_numbering = bool(
        re.match(r"^\s*\d+[.)]\s*", raw_line)
    )

    if not has_numbering:
        return False

    # A short heading without sentence punctuation or
    # a clear modal verb is treated as a section heading.
    heading_words = cleaned_line.split()

    modal_or_action_words = {
        "may", "might", "could", "will", "should",
        "cannot", "can't", "must", "is", "are",
        "has", "have", "was", "were"
    }

    contains_sentence_word = any(
        word.casefold() in modal_or_action_words
        for word in heading_words
    )

    has_sentence_punctuation = bool(
        re.search(r"[.!?]$", cleaned_line)
    )

    return (
        2 <= len(heading_words) <= 6
        and not contains_sentence_word
        and not has_sentence_punctuation
    )


def get_risk_category(line):
    """Return the first matching risk category."""

    category_priority = [
        "Testing Risk",
        "Dependency Risk",
        "Resource Risk",
        "Schedule Risk",
    ]

    matched_categories = []

    for category, patterns in RISK_PATTERNS.items():

        if any(
            re.search(pattern, line, re.IGNORECASE)
            for pattern in patterns
        ):
            matched_categories.append(category)

    for category in category_priority:

        if category in matched_categories:
            return category

    return None


def canonical_risk(description):
    """Create a key to consolidate closely related risk statements."""

    text = normalize_text(description).casefold()

    if (
        "not enough time to test" in text
        or "insufficient time to test" in text
        or "insufficient time for testing" in text
        or "may not complete testing" in text
    ):
        return "insufficient_testing_time"

    if (
        "deadline may be missed" in text
        or "may miss the deadline" in text
        or "may miss sprint deadline" in text
        or "may not finish on time" in text
    ):
        return "deadline_at_risk"

    return text


def detect_risks(text):
    """
    Detect potential project risks.

    Returns:
        [
            {
                "category": "Schedule Risk",
                "description": "..."
            }
        ]
    """

    if not text or not str(text).strip():
        return []

    risks = []
    seen_risks = set()

    for raw_line in str(text).splitlines():

        if not normalize_text(raw_line):
            continue

        # Clean bullets, numbering and discussion prefixes.
        line = clean_risk_line(raw_line)

        if not line:
            continue

        # Ignore numbered section headings.
        if is_heading_only(raw_line, line):
            continue

        # Ignore explicitly labelled issues and tasks.
        if is_non_risk_entry(line):
            continue

        category = get_risk_category(line)

        if category is None:
            continue

        risk_key = canonical_risk(line)

        if risk_key in seen_risks:
            continue

        risks.append({
            "category": category,
            "description": line,
        })

        seen_risks.add(risk_key)

    return risks
