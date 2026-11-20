
import re


def normalize_text(text):
    """Normalize whitespace."""
    return re.sub(r"\s+", " ", str(text or "")).strip()


def normalize_key(text):
    """Normalize text for comparison and deduplication."""
    text = normalize_text(text).casefold()

    # Remove bullets and numbering.
    text = re.sub(r"^[\s#>*•\-–—\d.)]+", "", text)

    # Remove common entry labels.
    text = re.sub(
        r"^(issue|discussion|blocker|risk|decision|action item|todo)\s*:\s*",
        "",
        text
    )

    return text.strip()


def get_blocker_key(line):
    text = normalize_key(line)

    if "test server" in text and any(
        word in text for word in [
            "unavailable", "cannot continue",
            "cannot proceed", "blocked", "access"
        ]
    ):
        return "test_server_unavailable"

    if "approval" in text and any(
        word in text for word in [
            "pending", "waiting", "not received", "blocked"
        ]
    ):
        return "approval_pending"

    return text


def get_action_key(line):
    """Group genuinely duplicate action items."""

    text = normalize_key(line)

    if "database documentation" in text:
        return "complete_database_documentation"

    # Keep preparation and completion as separate tasks.
    if "test cases" in text:
        if "prepare" in text:
            return "prepare_test_cases"

        if any(word in text for word in ["finish", "complete"]):
            return "complete_test_cases"

    if "test server" in text and "access" in text:
        return "restore_test_server_access"

    if "api approval" in text:
        return "obtain_api_approval"

    return text


def is_short_issue_label(line):
    text = normalize_key(line)

    short_labels = {
        "dependency approval pending",
        "approval pending",
        "test server unavailable",
        "testing behind schedule",
        "server unavailable",
        "no blocker reported",
        "decision recorded",
    }

    return text in short_labels


def identify_blockers_and_actions(text):
    """
    Extract blockers and action items separately.
    """

    if not text or not str(text).strip():
        return {
            "blockers": [],
            "action_items": [],
        }

    lines = [
        normalize_text(line)
        for line in str(text).splitlines()
        if normalize_text(line)
    ]

    blocker_pattern = re.compile(
        r"\b("
        r"blocked by|"
        r"blocked because|"
        r"cannot proceed|"
        r"unable to proceed|"
        r"waiting for approval|"
        r"approval is still pending|"
        r"approval pending|"
        r"work is blocked|"
        r"access is unavailable|"
        r"server is unavailable|"
        r"test server unavailable|"
        r"preventing progress|"
        r"testing cannot continue|"
        r"cannot continue testing|"
        r"dependency approval pending"
        r")\b",
        re.IGNORECASE,
    )

    action_pattern = re.compile(
        r"\b("
        r"action item|"
        r"to do|todo|"
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

    blockers_by_key = {}
    actions_by_key = {}

    for line in lines:

        normalized = normalize_key(line)

        if is_short_issue_label(line):
            continue

        # Extract blockers.
        if blocker_pattern.search(line):
            key = get_blocker_key(line)

            existing = blockers_by_key.get(key)

            if existing is None or len(line) > len(existing):
                blockers_by_key[key] = line

        # Ignore CSV header rows.
        if (
            "meeting date" in normalized
            and "action item" in normalized
            and "owner" in normalized
        ):
            continue

        # Extract action items.
        if action_pattern.search(line):
            key = get_action_key(line)

            existing = actions_by_key.get(key)

            if existing is None or len(line) > len(existing):
                actions_by_key[key] = line

    return {
        "blockers": list(blockers_by_key.values()),
        "action_items": list(actions_by_key.values()),
    }
