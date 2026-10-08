import csv
import os
from datetime import datetime


EVENT_FILE = "events.csv"


def initialize_event_log():
    """Create the event log file with headers if it does not exist."""

    if not os.path.exists(EVENT_FILE):

        with open(
            EVENT_FILE,
            "w",
            newline="",
            encoding="utf-8"
        ) as file:

            writer = csv.writer(file)

            writer.writerow([
                "timestamp",
                "event_type",
                "incident_id",
                "location",
                "risk_level",
                "risk_score",
                "reason"
            ])


def log_event(
    event_type,
    incident_id,
    location,
    risk_level,
    risk_score,
    reason
):
    """Save an explainable AI event."""

    initialize_event_log()

    with open(
        EVENT_FILE,
        "a",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.writer(file)

        writer.writerow([
            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            event_type,
            incident_id,
            location,
            risk_level,
            risk_score,
            reason
        ])


def get_events():

    initialize_event_log()

    events = []

    with open(
        EVENT_FILE,
        "r",
        newline="",
        encoding="utf-8"
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:
            events.append(row)

    return events
if __name__ == "__main__":
    initialize_event_log()
    print("events.csv created successfully.")