# ============================================
# CampusGuardian AI - Emergency Response
# ============================================

def generate_emergency_response(
    category,
    risk_level,
    location,
    description,
    emergency=False
):
    """Generate immediate response actions for an incident."""

    category_lower = category.lower()
    actions = []

    # FIRE
    if "fire" in category_lower:
        actions = [
            "Activate the campus fire emergency protocol.",
            f"Evacuate students and staff from {location}.",
            "Alert campus security and the fire response team.",
            "Keep people away from smoke and flames.",
            "Contact the fire department if required.",
            "Do not allow re-entry until the area is declared safe."
        ]

    # MEDICAL
    elif "medical" in category_lower:
        actions = [
            "Alert campus security immediately.",
            f"Send first-aid support to {location}.",
            "Contact the campus medical team.",
            "Keep the area clear for medical access.",
            "Call emergency medical services if required.",
            "Record the response and update the incident status."
        ]

    # LIFT / ELEVATOR
    elif "lift" in category_lower or "elevator" in category_lower:
        actions = [
            "Immediately alert campus security and maintenance.",
            f"Secure the lift area at {location}.",
            "Do not allow anyone to force open or operate the lift.",
            "Contact the authorised elevator maintenance team.",
            "If people are trapped or injured, contact emergency services.",
            "Keep the incident OPEN until the lift is inspected and safe."
        ]

    # ACCIDENT
    elif "accident" in category_lower:
        actions = [
            "Secure the accident area immediately.",
            f"Keep students and staff away from {location}.",
            "Alert campus security and medical personnel.",
            "Provide first aid if required.",
            "Contact emergency services for serious injuries.",
            "Document the incident and update its status."
        ]

    # VIOLENCE / HARASSMENT
    elif "violence" in category_lower or "harassment" in category_lower:
        actions = [
            "Alert campus security immediately.",
            f"Secure the affected area at {location}.",
            "Prioritise the safety of students and staff.",
            "Do not allow untrained personnel to intervene physically.",
            "Contact appropriate authorities when required.",
            "Record the incident securely and monitor its status."
        ]

    # THEFT
    elif "theft" in category_lower:
        actions = [
            "Alert campus security.",
            f"Secure and monitor {location}.",
            "Preserve available evidence such as CCTV footage.",
            "Identify and record relevant witnesses.",
            "Escalate to authorities if required.",
            "Update the incident after investigation."
        ]

    # ELECTRICITY
    elif "electric" in category_lower:
        actions = [
            "Alert the electrical maintenance team.",
            f"Restrict access to the affected area at {location}.",
            "Do not allow students to touch electrical equipment.",
            "Switch off the affected power source if safely possible.",
            "Inspect the electrical system before restoring access.",
            "Mark the incident RESOLVED only after safety verification."
        ]

    # WATER
    elif "water" in category_lower:
        actions = [
            "Alert campus maintenance immediately.",
            f"Restrict access around {location}.",
            "Identify and isolate the water source if safely possible.",
            "Protect nearby electrical equipment.",
            "Clean and inspect the affected area.",
            "Update the incident after the leakage is controlled."
        ]

    # GARBAGE / WASTE
    elif "garbage" in category_lower or "waste" in category_lower:
        actions = [
            "Notify campus housekeeping.",
            f"Inspect the affected location: {location}.",
            "Remove accumulated waste safely.",
            "Check whether the issue creates a health or fire risk.",
            "Increase cleaning frequency if necessary.",
            "Update the incident after cleanup."
        ]

    # POTHOLE
    elif "pothole" in category_lower:
        actions = [
            "Alert campus maintenance.",
            f"Place a temporary warning near {location}.",
            "Restrict traffic if the pothole creates immediate danger.",
            "Schedule road repair.",
            "Verify the repaired surface.",
            "Update the incident after repair."
        ]

    # STREETLIGHT
    elif "streetlight" in category_lower:
        actions = [
            "Notify the electrical maintenance team.",
            f"Inspect the streetlight at {location}.",
            "Place temporary safety lighting if necessary.",
            "Repair or replace the faulty light.",
            "Check surrounding visibility after repair.",
            "Update the incident after verification."
        ]

    # DEFAULT
    else:
        actions = [
            "Alert the responsible campus department.",
            f"Inspect the reported location: {location}.",
            "Keep students and staff away if there is a safety risk.",
            "Take appropriate corrective action.",
            "Monitor the situation.",
            "Update the incident status after resolution."
        ]

    # Emergency escalation
    if emergency:
        actions.insert(
            0,
            "🚨 EMERGENCY: Activate the campus emergency response protocol immediately."
        )

    # Critical escalation
    elif risk_level.upper() == "CRITICAL":
        actions.insert(
            0,
            "⚠️ CRITICAL RISK: Escalate this incident immediately."
        )

    return actions


def get_emergency_message(risk_level, emergency):
    """Return the appropriate emergency heading."""

    if emergency:
        return "🚨 EMERGENCY RESPONSE REQUIRED"

    if risk_level.upper() == "CRITICAL":
        return "🔴 CRITICAL INCIDENT — ACT NOW"

    if risk_level.upper() == "HIGH":
        return "🟠 HIGH RISK — IMMEDIATE ATTENTION REQUIRED"

    return "🟢 STANDARD RESPONSE"


# ============================================
# TEST
# ============================================

if __name__ == "__main__":

    response = generate_emergency_response(
        category="Lift/Elevator",
        risk_level="HIGH",
        location="A Block, 2nd Floor",
        description="Lift is stuck with students inside.",
        emergency=True
    )

    print("\n======================================")
    print(" CAMPUSGUARDIAN EMERGENCY RESPONSE")
    print("======================================")

    print("\nWHAT SHOULD WE DO NOW?\n")

    for number, action in enumerate(response, start=1):
        print(f"{number}. {action}")