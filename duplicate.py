from difflib import SequenceMatcher


def normalize_text(text):
    """Clean text before comparison."""

    return " ".join(text.lower().strip().split())


def calculate_similarity(text1, text2):
    """Calculate similarity between two descriptions."""

    text1 = normalize_text(text1)
    text2 = normalize_text(text2)

    return round(
        SequenceMatcher(None, text1, text2).ratio() * 100,
        2
    )


def is_duplicate(
    new_description,
    existing_description,
    new_location,
    existing_location,
    threshold=70
):
    """
    Determine whether two incident reports are likely duplicates.
    """

    description_similarity = calculate_similarity(
        new_description,
        existing_description
    )

    location_similarity = calculate_similarity(
        new_location,
        existing_location
    )

    # Location is important when identifying campus incidents.
    combined_score = (
        description_similarity * 0.7
        + location_similarity * 0.3
    )

    duplicate = combined_score >= threshold

    return {
        "is_duplicate": duplicate,
        "description_similarity": description_similarity,
        "location_similarity": location_similarity,
        "combined_score": round(combined_score, 2)
    }


def find_duplicate(new_incident, existing_incidents):
    """
    Compare a new incident against existing incidents.
    """

    best_match = None
    highest_score = 0

    for incident in existing_incidents:

        result = is_duplicate(
            new_incident["description"],
            incident["description"],
            new_incident["location"],
            incident["location"]
        )

        if result["combined_score"] > highest_score:
            highest_score = result["combined_score"]

            best_match = {
                "incident_id": incident["id"],
                "score": result["combined_score"],
                "is_duplicate": result["is_duplicate"]
            }

    return best_match


if __name__ == "__main__":

    new_report = {
        "description": "Street light is not working near Block A",
        "location": "Block A"
    }

    old_report = {
        "id": 1,
        "description": "Broken streetlight near Block A",
        "location": "Block A"
    }

    result = is_duplicate(
        new_report["description"],
        old_report["description"],
        new_report["location"],
        old_report["location"]
    )

    print("CampusGuardian Duplicate Detection")
    print("-----------------------------------")
    print("Description Similarity:",
          result["description_similarity"], "%")
    print("Location Similarity:",
          result["location_similarity"], "%")
    print("Combined Score:",
          result["combined_score"], "%")
    print("Duplicate:",
          result["is_duplicate"])