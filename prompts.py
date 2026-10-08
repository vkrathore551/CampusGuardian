def generate_why_explanation(
    category,
    description,
    risk_score,
    risk_level
):
    """Explain why an incident received its risk level."""

    explanation = (
        f"This incident was classified as {risk_level} risk "
        f"with a risk score of {risk_score}/100. "
    )

    category_reasons = {
        "fire": "Fire-related incidents can spread quickly and may cause injuries or property damage.",
        "medical": "A medical emergency may require immediate assistance to protect the person's safety.",
        "accident": "Accidents can result in injuries and may create additional safety risks.",
        "violence": "Violent incidents may threaten the safety of students, staff, and visitors.",
        "theft": "Theft can create security concerns and may indicate a wider safety issue.",
        "harassment": "Harassment reports can affect personal safety and student wellbeing.",
        "garbage": "Accumulated garbage can create hygiene, health, and environmental risks.",
        "pothole": "A pothole can cause vehicle or pedestrian accidents if it is not repaired.",
        "streetlight": "A broken streetlight can reduce visibility and increase safety risks.",
        "water leakage": "Water leakage can cause slippery surfaces, property damage, and electrical hazards."
    }

    reason = category_reasons.get(
        category.lower(),
        "The reported incident may require attention from the responsible campus department."
    )

    explanation += reason

    if "fire" in description.lower() or "smoke" in description.lower():
        explanation += " The presence of fire or smoke increases the urgency of the situation."

    if "injured" in description.lower() or "injury" in description.lower():
        explanation += " Reported injuries require immediate attention."

    if risk_score >= 75:
        explanation += " Immediate response is recommended."

    return explanation


def generate_action_plan(
    category,
    risk_level,
    location,
    emergency=False
):
    """Generate an immediate response plan."""

    if emergency or risk_level == "CRITICAL":
        return (
            f"1. Alert campus security immediately.\n"
            f"2. Send an emergency response team to {location}.\n"
            f"3. Keep students and staff away from the affected area.\n"
            f"4. Contact appropriate emergency services if required.\n"
            f"5. Update the incident status after response."
        )

    if risk_level == "HIGH":
        return (
            f"1. Notify the responsible department.\n"
            f"2. Send a response team to {location}.\n"
            f"3. Secure the affected area if necessary.\n"
            f"4. Update the incident status after inspection."
        )

    if category.lower() == "garbage":
        return (
            f"1. Assign sanitation staff.\n"
            f"2. Inspect the reported location: {location}.\n"
            f"3. Remove the accumulated waste.\n"
            f"4. Mark the incident as resolved after verification."
        )

    if category.lower() == "pothole":
        return (
            f"1. Assign the civil maintenance team.\n"
            f"2. Inspect the pothole at {location}.\n"
            f"3. Place a temporary warning if necessary.\n"
            f"4. Repair the road and verify the fix."
        )

    if category.lower() == "streetlight":
        return (
            f"1. Assign electrical maintenance.\n"
            f"2. Inspect the streetlight at {location}.\n"
            f"3. Repair or replace the faulty component.\n"
            f"4. Verify that the light is working."
        )

    return (
        f"1. Assign the appropriate campus department.\n"
        f"2. Inspect the incident at {location}.\n"
        f"3. Take the required corrective action.\n"
        f"4. Update the incident status."
    )


def generate_incident_summary(
    category,
    description,
    location,
    risk_level,
    priority
):
    """Generate a short incident summary."""

    return (
        f"{category.title()} incident reported at {location}. "
        f"Description: {description}. "
        f"Risk level: {risk_level}. "
        f"Priority: {priority}."
    )


if __name__ == "__main__":

    category = "fire"
    description = "Smoke detected near the chemistry laboratory"
    location = "Chemistry Block"

    risk_score = 90
    risk_level = "CRITICAL"
    priority = "CRITICAL"

    print("CampusGuardian AI Explanation Engine")
    print("------------------------------------")

    print("\nWHY?")
    print(
        generate_why_explanation(
            category,
            description,
            risk_score,
            risk_level
        )
    )

    print("\nWHAT SHOULD WE DO NOW?")
    print(
        generate_action_plan(
            category,
            risk_level,
            location,
            emergency=True
        )
    )

    print("\nSUMMARY")
    print(
        generate_incident_summary(
            category,
            description,
            location,
            risk_level,
            priority
        )
    )