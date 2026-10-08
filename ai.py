from scoring import (
    calculate_risk_score,
    get_priority,
    get_department,
    get_recommended_action
)

from prompts import (
    generate_why_explanation,
    generate_action_plan,
    generate_incident_summary
)


def analyze_incident(
    description,
    category,
    location,
    emergency=False
):
    """
    Analyze a campus incident and generate
    risk, priority, department and action.
    """

    # 1. Calculate risk
    risk_score, risk_level = calculate_risk_score(
        category=category,
        description=description,
        emergency=emergency
    )

    # 2. Calculate priority
    priority = get_priority(risk_score)

    # 3. Assign department
    department = get_department(category)

    # 4. Generate recommended action
    recommended_action = get_recommended_action(
        risk_level,
        category
    )

    # 5. Generate WHY explanation
    why_explanation = generate_why_explanation(
        category=category,
        description=description,
        risk_score=risk_score,
        risk_level=risk_level
    )

    # 6. Generate action plan
    action_plan = generate_action_plan(
        category=category,
        risk_level=risk_level,
        location=location,
        emergency=emergency
    )

    # 7. Generate summary
    summary = generate_incident_summary(
        category=category,
        description=description,
        location=location,
        risk_level=risk_level,
        priority=priority
    )

    return {
        "category": category,
        "description": description,
        "location": location,
        "risk_score": risk_score,
        "risk_level": risk_level,
        "priority": priority,
        "department": department,
        "recommended_action": recommended_action,
        "why": why_explanation,
        "action_plan": action_plan,
        "summary": summary,
        "emergency": emergency
    }


if __name__ == "__main__":

    result = analyze_incident(
        description="Smoke detected near the chemistry laboratory",
        category="fire",
        location="Chemistry Block",
        emergency=True
    )

    print("\n===================================")
    print("     CAMPUSGUARDIAN AI ANALYSIS")
    print("===================================")

    print("\nCategory:")
    print(result["category"])

    print("\nRisk Score:")
    print(result["risk_score"], "/ 100")

    print("\nRisk Level:")
    print(result["risk_level"])

    print("\nPriority:")
    print(result["priority"])

    print("\nDepartment:")
    print(result["department"])

    print("\nWHY?")
    print(result["why"])

    print("\nWHAT SHOULD WE DO NOW?")
    print(result["action_plan"])

    print("\nSummary:")
    print(result["summary"])