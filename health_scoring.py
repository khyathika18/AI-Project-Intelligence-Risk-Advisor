import re

def get_items(data, *keys):
    """Get a list from a dictionary, ignoring key capitalization."""
    if not isinstance(data, dict):
        return []
    normalized = {str(key).lower(): value for key, value in data.items()}
    for key in keys:
        value = normalized.get(key.lower(), [])
        if isinstance(value, list):
            return value
        if isinstance(value, str) and value.strip():
            return [value]
    return []

def count_schedule_risks(risks):
    count = 0
    if not isinstance(risks, list):
        return count
    for risk in risks:
        if isinstance(risk, dict):
            if str(risk.get("status", "Active")).casefold() == "resolved":
                continue
            category = str(risk.get("category", "")).lower()
            description = str(risk.get("description", "")).lower()
        else:
            category, description = "", str(risk).lower()
        if (
            "schedule" in category or "deadline" in description
            or "behind schedule" in description
            or "miss the sprint deadline" in description
        ):
            count += 1
    return count

def _is_active_blocker(blocker):
    if isinstance(blocker, dict):
        return str(blocker.get("status", "Open")).casefold() not in {
            "resolved", "closed", "done"
        }
    return bool(str(blocker).strip())

def detect_milestone_conflicts(milestones):
    """Detect conflicting testing milestones specifying different weeks."""
    testing_weeks = set()
    for milestone in milestones:
        text = str(milestone).lower()
        if "test" in text:
            testing_weeks.update(
                int(week) for week in re.findall(r"\bweek\s+(\d+)\b", text)
            )
    return len(testing_weeks) > 1

def calculate_health_score(scope_results, risks, blockers):
    """
    Calculate a 100-point project health score.

    Pass only currently active blockers in `blockers`. Resolved historical
    blockers may be supplied as dictionaries with status='Resolved'; they
    are excluded from the active blocker count.
    """
    goals = get_items(scope_results, "goals", "objectives")
    deliverables = get_items(scope_results, "deliverables")
    milestones = get_items(scope_results, "milestones")

    scope_score = (
        (10 if goals else 0)
        + (10 if deliverables else 0)
        + (10 if milestones else 0)
    )

    schedule_risks = count_schedule_risks(risks)
    timeline_score = 40 - min(schedule_risks * 10, 20)
    milestone_conflict = detect_milestone_conflicts(milestones)
    if milestone_conflict:
        timeline_score -= 10
    timeline_score = max(timeline_score, 0)

    if not isinstance(blockers, list):
        blockers = []
    active_blockers = [item for item in blockers if _is_active_blocker(item)]
    blocker_count = len(active_blockers)
    blocker_score = max(30 - blocker_count * 10, 0)

    overall_score = scope_score + timeline_score + blocker_score
    if overall_score >= 80:
        health_status = "Healthy"
    elif overall_score >= 60:
        health_status = "Moderate"
    else:
        health_status = "At Risk"

    return {
        "overall_score": overall_score,
        "health_status": health_status,
        "scope_score": scope_score,
        "scope_max": 30,
        "timeline_score": timeline_score,
        "timeline_max": 40,
        "blocker_score": blocker_score,
        "blocker_max": 30,
        "schedule_risks": schedule_risks,
        "milestone_conflict": milestone_conflict,
        "blocker_count": blocker_count,
    }
