
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
        r"\bdeadline.{0,80}(?:at risk|missed|delay)\b",
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
        r"\bwaiting for .*dependency approval\b",
        r"\bwaiting for dependency approval\b",
        r"\bdependency approval (?:is )?pending\b",
        r"\bawaiting .*dependency approval\b",
        r"\bdependency approval delayed\b",
        r"\bdependency not approved\b",
        r"\bdependency is pending\b",
        r"\bwaiting for .*approval\b",
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
    """Normalize whitespace and safely handle empty values."""
    return re.sub(r"\s+", " ", str(text or "")).strip()


def clean_risk_line(line):
    """Remove bullets, numbering, and discussion labels."""
    line = normalize_text(line)

    # Remove bullet symbols.
    line = re.sub(r"^[•●▪◦*\-]+\s*", "", line)

    # Remove numbering such as 1. or 2)
    line = re.sub(r"^\d+[.)]\s*", "", line)

    # Remove Discussion: prefix.
    line = re.sub(
        r"^Discussion\s*:\s*",
        "",
        line,
        flags=re.IGNORECASE,
    )

    return normalize_text(line)


def is_non_risk_entry(line):
    """Ignore entries explicitly labelled as issues, actions, or decisions."""
    text = normalize_text(line).casefold()

    prefixes = (
        "issue:",
        "action item:",
        "blocker:",
        "decision:",
        "todo:",
    )

    return text.startswith(prefixes)


def is_heading_only(raw_line, cleaned_line):
    """Ignore short numbered headings rather than treating them as risks."""
    has_numbering = bool(
        re.match(r"^\s*\d+[.)]\s*", raw_line)
    )

    if not has_numbering:
        return False

    words = cleaned_line.split()

    modal_words = {
        "may", "might", "could", "will", "should",
        "cannot", "can't", "must", "is", "are",
        "has", "have", "was", "were",
    }

    has_sentence_word = any(
        word.casefold() in modal_words
        for word in words
    )

    has_punctuation = bool(
        re.search(r"[.!?]$", cleaned_line)
    )

    return (
        2 <= len(words) <= 6
        and not has_sentence_word
        and not has_punctuation
    )


def get_risk_category(line):
    """Identify the most specific matching risk category."""
    priority = [
        "Testing Risk",
        "Dependency Risk",
        "Resource Risk",
        "Schedule Risk",
    ]

    matches = [
        category
        for category, patterns in RISK_PATTERNS.items()
        if any(
            re.search(pattern, line, re.IGNORECASE)
            for pattern in patterns
        )
    ]

    return next(
        (category for category in priority if category in matches),
        None,
    )


def canonical_risk(description):
    """Create a common key for descriptions referring to the same risk."""
    text = normalize_text(description).casefold()

    # Similar testing-risk descriptions.
    if any(term in text for term in (
        "not enough time to test",
        "insufficient time to test",
        "insufficient time for testing",
        "may not complete testing",
    )):
        return "insufficient_testing_time"

    # Similar deadline-risk descriptions.
    if any(term in text for term in (
        "deadline may be missed",
        "may miss the deadline",
        "may miss sprint deadline",
        "may not finish on time",
        "deadline is at risk",
    )):
        return "deadline_at_risk"

    # Normalize remaining descriptions.
    text = re.sub(r"[^\w\s]", " ", text)
    return normalize_text(text)


def detect_risks(text):
    """
    Detect and deduplicate potential risks.

    Output format:
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
    seen = set()

    for raw_line in str(text).splitlines():
        if not normalize_text(raw_line):
            continue

        line = clean_risk_line(raw_line)

        if not line:
            continue

        if is_heading_only(raw_line, line):
            continue

        if is_non_risk_entry(line):
            continue

        category = get_risk_category(line)

        if category is None:
            continue

        key = (category, canonical_risk(line))

        if key not in seen:
            risks.append({
                "category": category,
                "description": line,
            })
            seen.add(key)

    return risks


def reconcile_risks(text, risks=None):
    """
    Add a status field to each detected risk.

    Risks remain Active unless the source contains explicit
    evidence that the corresponding risk has been resolved.

    For example, 'testing resumed' alone does not mean
    that all testing risks have been resolved.
    """
    source = str(text or "").casefold()

    risks = (
        detect_risks(text)
        if risks is None
        else list(risks)
    )

    reconciled = []

    for risk in risks:
        item = dict(risk)

        description = str(
            item.get("description", "")
        ).casefold()

        category = str(
            item.get("category", "")
        ).casefold()

        resolved = False

        # Testing risks require explicit testing completion.
        if category == "testing risk" or "testing" in description or "test cases" in description:
            resolved = any(phrase in source for phrase in (
                "all test cases completed",
                "testing completed successfully",
                "testing is complete",
                "all modules passed testing",
                "all testing activities completed",
            ))

        # Schedule risks require evidence that the schedule
        # or project deadline was successfully met.
        elif category == "schedule risk" or "deadline" in description or "schedule" in description:
            resolved = any(phrase in source for phrase in (
                "project delivered on time",
                "deadline met",
                "project completed",
                "schedule risk resolved",
                "project completed within schedule",
            ))

        # Dependency risks require explicit approval or
        # dependency completion evidence.
        elif category == "dependency risk" or "dependency" in description:
            resolved = any(phrase in source for phrase in (
                "dependency approved",
                "approval received",
                "approval granted",
                "dependency completed",
                "dependency resolved",
            ))

        # Resource risks require explicit resource recovery.
        elif category == "resource risk" or "resource" in description:
            resolved = any(phrase in source for phrase in (
                "resources allocated",
                "additional resources assigned",
                "staff shortage resolved",
                "team member available",
                "resource constraints resolved",
            ))

        item["status"] = (
            "Resolved" if resolved else "Active"
        )

        reconciled.append(item)

    return reconciled
