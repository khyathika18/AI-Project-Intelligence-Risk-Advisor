
import re


def clean_label(text):
    """Remove common labels from extracted statements."""

    text = str(text or "").strip()

    text = re.sub(
        r"^(project\s+)?(goal|objective|aim|deliverable|"
        r"submission|milestone|deadline|due date|timeline)\s*:\s*",
        "",
        text,
        flags=re.IGNORECASE,
    )

    return text.strip(" :-")


def get_value(data, *keys, default=""):
    """Get a dictionary value without depending on key capitalization."""

    if not isinstance(data, dict):
        return default

    normalized = {
        str(key).lower().replace(" ", "_"): value
        for key, value in data.items()
    }

    for key in keys:
        value = normalized.get(
            key.lower().replace(" ", "_")
        )

        if value is not None:
            return value

    return default


def generate_user_stories(scope_results):
    """Generate draft user stories from project scope."""

    stories = []

    if not isinstance(scope_results, dict):
        return stories

    goals = get_value(
        scope_results, "goals", "objectives", default=[]
    )

    deliverables = get_value(
        scope_results, "deliverables", default=[]
    )

    requirements = []

    for category in [goals, deliverables]:

        if isinstance(category, str):
            category = [category]

        if not isinstance(category, (list, tuple)):
            continue

        for item in category:

            requirement = clean_label(item)

            if requirement and requirement not in requirements:
                requirements.append(requirement)

    for index, requirement in enumerate(requirements, start=1):

        stories.append({
            "story_id": f"US-{index:03d}",
            "title": requirement,
            "user_role": "Project stakeholder (assumed)",
            "user_story": (
                f"As a project stakeholder, I want "
                f"{requirement.lower()} so that "
                f"the agreed project outcome can be achieved."
            ),
            "acceptance_criteria": (
                "Requirement implemented and tested; "
                "stakeholder approval required."
            ),
            "status": "Draft - requires stakeholder validation"
        })

    return stories


def generate_risk_register(risks):
    """Convert detected risks into a structured risk register."""

    risk_register = []

    if isinstance(risks, dict):
        risks = risks.get("risks", [])

    if isinstance(risks, (str, dict)):
        risks = [risks]

    if not isinstance(risks, (list, tuple)):
        return risk_register

    for risk in risks:

        if isinstance(risk, dict):

            category = get_value(
                risk, "category", "risk_category",
                default="Uncategorized"
            )

            description = get_value(
                risk, "description", "details", "risk",
                default=""
            )

        else:
            category = "Uncategorized"
            description = str(risk)

        description = str(description).strip()

        if not description:
            continue

        risk_register.append({
            "risk_id": f"R-{len(risk_register) + 1:03d}",
            "category": str(category),
            "description": description,
            "probability": "Not assessed",
            "impact": "Not assessed",
            "severity": "Not assessed",
            "mitigation": "Not specified in source documents",
            "owner": "Not specified in source documents"
        })

    return risk_register


def extract_owner(action):
    """Extract explicitly assigned action owner."""

    patterns = [
        r"\bAssigned to\s+([A-Za-z][A-Za-z .'-]*?)(?=[:,;.]|$)",
        r"\bOwner\s*:\s*([A-Za-z][A-Za-z .'-]*?)(?=[:,;.]|$)"
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            str(action),
            re.IGNORECASE
        )

        if match:
            return match.group(1).strip()

    return "Not specified"


def extract_deadline(action):
    """Extract a clearly stated deadline."""

    patterns = [
        r"\bWeek\s+\d+\b",
        r"\b\d{4}-\d{2}-\d{2}\b",
        r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
        r"\b\d{1,2}\s+"
        r"(?:January|February|March|April|May|June|July|August|"
        r"September|October|November|December)\s+\d{4}\b"
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            str(action),
            re.IGNORECASE
        )

        if match:
            return match.group(0)

    return "Not specified"


def generate_action_item_report(action_items):
    """Convert action items into a structured report."""

    report = []

    if isinstance(action_items, str):
        action_items = [action_items]

    if not isinstance(action_items, (list, tuple)):
        return report

    for item in action_items:

        if isinstance(item, dict):

            task = get_value(
                item, "task", "description", "action",
                default=""
            )

            owner = get_value(
                item, "owner", "assigned_to",
                default=""
            )

            deadline = get_value(
                item, "deadline", "due_date",
                default=""
            )

        else:

            task = str(item)
            owner = ""
            deadline = ""

        task = str(task).strip()

        if not task:
            continue

        report.append({
            "action_id": f"A-{len(report) + 1:03d}",
            "task": task,
            "owner": str(owner).strip() or extract_owner(task),
            "deadline": str(deadline).strip() or extract_deadline(task),
            "priority": "Not specified",
            "status": "Not specified"
        })

    return report


def generate_documentation(scope_results, risks, action_items):
    """Generate all three project documentation reports."""

    return {
        "user_stories": generate_user_stories(scope_results),
        "risk_register": generate_risk_register(risks),
        "action_item_report": generate_action_item_report(action_items)
    }
