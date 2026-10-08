def calculate_risk_score(
    category,
    description,
    emergency=False
):
    """
    Calculate an AI-style risk score for a campus incident.

    Score range: 0 - 100
    """

    score = 20

    category = category.lower()
    description = description.lower()

    # Category-based scoring
    category_scores = {
        "fire": 40,
        "medical": 35,
        "accident": 35,
        "violence": 40,
        "theft": 25,
        "harassment": 30,
        "electricity": 30,
        "water leakage": 20,
        "garbage": 15,
        "pothole": 15,
        "streetlight": 10
    }

    score += category_scores.get(category, 10)

    # Emergency incident
    if emergency:
        score += 25

    # Important risk words
    high_risk_words = [
        "fire",
        "smoke",
        "injured",
        "injury",
        "accident",
        "blood",
        "weapon",
        "violence",
        "unconscious",
        "danger",
        "explosion"
    ]

    for word in high_risk_words:
        if word in description:
            score += 5

    # Limit score to 100
    score = min(score, 100)

    # Determine risk level
    if score >= 75:
        risk_level = "CRITICAL"
    elif score >= 50:
        risk_level = "HIGH"
    elif score >= 30:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    return score, risk_level


def get_priority(risk_score):
    """Convert risk score into incident priority."""

    if risk_score >= 75:
        return "CRITICAL"

    elif risk_score >= 50:
        return "HIGH"

    elif risk_score >= 30:
        return "MEDIUM"

    else:
        return "LOW"


def get_recommended_action(risk_level, category):
    """Generate an emergency response recommendation."""

    category = category.lower()

    if risk_level == "CRITICAL":
        return (
            "Immediately alert campus security and emergency services. "
            "Secure the affected area and provide emergency assistance."
        )

    if risk_level == "HIGH":
        return (
            "Immediately notify the responsible department and campus security. "
            "Send a response team to the reported location."
        )

    if category == "garbage":
        return "Assign sanitation staff to inspect and clear the reported area."

    if category == "pothole":
        return "Assign the maintenance department to inspect and repair the road."

    if category == "streetlight":
        return "Assign the electrical maintenance team to inspect the streetlight."

    if category == "water leakage":
        return "Assign the plumbing/maintenance team to inspect and stop the leakage."

    return "Assign the appropriate campus department for investigation."


def get_department(category):
    """Automatically assign the incident to a department."""

    category = category.lower()

    departments = {
        "fire": "Emergency Services",
        "medical": "Medical Center",
        "accident": "Campus Security",
        "violence": "Campus Security",
        "theft": "Campus Security",
        "harassment": "Student Welfare",
        "electricity": "Electrical Maintenance",
        "water leakage": "Maintenance",
        "garbage": "Sanitation",
        "pothole": "Civil Maintenance",
        "streetlight": "Electrical Maintenance"
    }

    return departments.get(category, "Campus Administration")


if __name__ == "__main__":

    score, risk = calculate_risk_score(
        category="fire",
        description="Smoke and fire reported near the laboratory",
        emergency=True
    )

    priority = get_priority(score)

    action = get_recommended_action(
        risk,
        "fire"
    )

    department = get_department("fire")

    print("CampusGuardian AI Risk Engine")
    print("------------------------------")
    print("Risk Score:", score)
    print("Risk Level:", risk)
    print("Priority:", priority)
    print("Department:", department)
    print("Recommended Action:", action)