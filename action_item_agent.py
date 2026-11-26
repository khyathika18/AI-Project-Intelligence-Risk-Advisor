
import re
from datetime import datetime


def normalize_text(text):
    """Normalize whitespace."""
    return re.sub(r"\s+", " ", str(text or "")).strip()


def clean_action_text(text):
    """Remove bullets, numbering, and action-item labels."""
    text = normalize_text(text)

    # Remove leading bullets and numbering.
    text = re.sub(r"^[\s#>*•▪●◦\-–—\d.)]+", "", text)

    # Remove common action labels.
    text = re.sub(
        r"^(?:action\s*item|todo|to\s*do)\s*:\s*",
        "",
        text,
        flags=re.IGNORECASE,
    )

    return text.strip()


def normalize_key(text):
    """Normalize text for comparison and deduplication."""
    text = normalize_text(text).casefold()

    text = re.sub(r"^[\s#>*•▪●◦\-–—\d.)]+", "", text)

    text = re.sub(
        r"^(issue|discussion|blocker|risk|decision|action item|todo)\s*:\s*",
        "",
        text,
    )

    return text.strip()


def _event_date(line):
    """Extract a date when one is explicitly written in a line."""
    patterns = [
        (
            r"\b(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})\b",
            "%d %B %Y",
        ),
        (
            r"\b(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{4})\b",
            "%d %b %Y",
        ),
        (
            r"\b(\d{4})-(\d{2})-(\d{2})\b",
            "%Y-%m-%d",
        ),
    ]

    for pattern, date_format in patterns:
        match = re.search(pattern, line, re.IGNORECASE)

        if match:
            try:
                return datetime.strptime(match.group(0), date_format)
            except ValueError:
                pass

    return None


def _event_rank(line, position):
    """Rank blocker events using dates and document position."""
    date_value = _event_date(line)

    if date_value:
        return (1, date_value.timestamp(), position)

    return (0, 0, position)


def get_blocker_key(line):
    """Generate a common key for related blocker descriptions."""
    text = normalize_key(line)

    if "test server" in text or (
        "server" in text and "testing" in text
    ):
        return "test_server_access"

    if "approval" in text or "dependency" in text:
        return "approval_pending"

    return text


def get_action_key(line):
    """Generate a common key for related action items."""
    text = normalize_key(line)

    if "database documentation" in text:
        return "complete_database_documentation"

    if "test cases" in text:
        if "prepare" in text:
            return "prepare_test_cases"

        if any(word in text for word in ("finish", "complete", "must")):
            return "complete_test_cases"

    if "test server" in text and "access" in text:
        return "restore_test_server_access"

    if "api approval" in text:
        return "obtain_api_approval"

    return text


def is_short_issue_label(line):
    """Identify short issue labels that should not become blockers."""
    text = normalize_key(line)

    return text in {
        "dependency approval pending",
        "approval pending",
        "test server unavailable",
        "testing behind schedule",
        "server unavailable",
        "no blocker reported",
        "decision recorded",
    }


def _classify_blocker_event(line):
    """Classify explicit blocker events as Open or Resolved."""
    text = normalize_text(line).casefold()

    if not any(
        term in text
        for term in ("server", "approval", "dependency", "testing")
    ):
        return None

    # Test-server resolution evidence.
    test_server_resolution_phrases = (
        "restored test server",
        "test server access restored",
        "server access restored",
        "server is available",
        "server became available",
        "testing resumed",
        "resumed testing",
        "test server restored",
        "access has been restored",
    )

    if any(phrase in text for phrase in test_server_resolution_phrases):
        if (
            "server" in text
            or "testing resumed" in text
            or "resumed testing" in text
        ):
            return ("test_server_access", "Resolved")

    # Test-server blocker evidence.
    test_server_open_phrases = (
        "test server unavailable",
        "server is unavailable",
        "testing cannot continue",
        "cannot continue testing",
        "testing is blocked",
        "blocked because the test server",
        "test server is down",
    )

    if any(phrase in text for phrase in test_server_open_phrases):
        return ("test_server_access", "Open")

    # Approval resolution evidence.
    approval_resolution_phrases = (
        "approval received",
        "approval was granted",
        "approval granted",
        "approval completed",
        "dependency approved",
    )

    if any(phrase in text for phrase in approval_resolution_phrases):
        return ("approval_pending", "Resolved")

    # Approval blocker evidence.
    approval_open_phrases = (
        "approval pending",
        "waiting for approval",
        "waiting for dependency approval",
        "approval is still pending",
        "not received approval",
    )

    if any(phrase in text for phrase in approval_open_phrases):
        return ("approval_pending", "Open")

    return None


def identify_blockers_and_actions(text):
    """
    Extract action items and reconcile blocker status.

    Returns active blockers, action items, resolved blockers,
    and blocker status evidence.
    """
    if not text or not str(text).strip():
        return {
            "blockers": [],
            "action_items": [],
            "resolved_blockers": [],
            "blocker_status": [],
        }

    lines = [
        normalize_text(line)
        for line in str(text).splitlines()
        if normalize_text(line)
    ]

    events = {}
    actions_by_key = {}

    # Recognize explicit action labels and common project tasks.
    action_pattern = re.compile(
        r"\b("
        r"action\s*item|"
        r"to\s*do|"
        r"todo|"
        r"must complete|"
        r"needs to be completed|"
        r"pending task|"
        r"follow up|"
        r"will complete|"
        r"assigned to|"
        r"obtain .* approval|"
        r"contact .* team|"
        r"restore .* access|"
        r"finish .* test cases|"
        r"complete .* documentation|"
        r"send .* progress update|"
        r"proceed with .* implementation|"
        r"confirm .* plan|"
        r"prepare .* test cases"
        r")\b",
        re.IGNORECASE,
    )

    for position, line in enumerate(lines):
        normalized = normalize_key(line)

        # Reconcile blocker events.
        event = _classify_blocker_event(line)

        if event:
            key, status = event
            rank = _event_rank(line, position)
            previous = events.get(key)

            if previous is None or rank > previous["rank"]:
                events[key] = {
                    "key": key,
                    "status": status,
                    "evidence": line,
                    "rank": rank,
                }

        # Skip table headings.
        if (
            "meeting date" in normalized
            and "action item" in normalized
            and "owner" in normalized
        ):
            continue

        # Skip short issue labels.
        if is_short_issue_label(line):
            continue

        # Extract and clean action items.
        if action_pattern.search(line):
            cleaned_action = clean_action_text(line)

            if not cleaned_action:
                continue

            key = get_action_key(line)
            previous = actions_by_key.get(key)

            if (
                previous is None
                or len(cleaned_action) > len(previous)
            ):
                actions_by_key[key] = cleaned_action

    # Build blocker status results.
    blocker_status = []
    active_blockers = []
    resolved_blockers = []

    for key, event in events.items():
        item = {
            "key": key,
            "status": event["status"],
            "description": event["evidence"],
        }

        blocker_status.append(item)

        if event["status"] == "Open":
            active_blockers.append(event["evidence"])
        else:
            resolved_blockers.append(event["evidence"])

    # Remove obsolete server-restoration actions after resolution.
    test_server_event = events.get("test_server_access")

    if (
        test_server_event
        and test_server_event["status"] == "Resolved"
    ):
        actions_by_key.pop("restore_test_server_access", None)

    return {
        "blockers": active_blockers,
        "action_items": list(actions_by_key.values()),
        "resolved_blockers": resolved_blockers,
        "blocker_status": blocker_status,
    }
