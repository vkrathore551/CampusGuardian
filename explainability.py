def explain_risk(
    risk_score,
    risk_level,
    category="Unknown",
    emergency=False,
    location="Unknown"
):
    """
    Generates a simple human-readable explanation
    for the AI risk assessment.
    """

    reasons = []

    try:
        score = float(risk_score)
    except:
        score = 0

    if score >= 80:
        reasons.append(
            "The incident has a very high risk score."
        )

    elif score >= 60:
        reasons.append(
            "The incident has a high risk score."
        )

    elif score >= 40:
        reasons.append(
            "The incident has a moderate risk score."
        )

    else:
        reasons.append(
            "The incident currently has a relatively low risk score."
        )

    if emergency:
        reasons.append(
            "The incident has been identified as an emergency."
        )

    if category and str(category).lower() != "unknown":
        reasons.append(
            f"The incident category is {category}."
        )

    if location and str(location).lower() != "unknown":
        reasons.append(
            f"The incident was reported at {location}."
        )

    explanation = " ".join(reasons)

    return explanation