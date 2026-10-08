import sqlite3
from datetime import datetime

DB_NAME = "campus_guardian.db"


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():
    connection = sqlite3.connect(DB_NAME)
    connection.row_factory = sqlite3.Row
    return connection


# ============================================================
# TABLE / MIGRATION HELPERS
# ============================================================

def _table_columns(connection, table_name="incidents"):
    rows = connection.execute(
        f"PRAGMA table_info({table_name})"
    ).fetchall()
    return {row[1] for row in rows}


def _add_missing_columns(connection):
    """Add newer columns without deleting existing incident data."""

    columns = _table_columns(connection)

    required_columns = {
        "title": "TEXT",
        "description": "TEXT",
        "category": "TEXT",
        "location": "TEXT",
        "latitude": "REAL",
        "longitude": "REAL",
        "priority": "TEXT",
        "risk_score": "INTEGER DEFAULT 0",
        "risk_level": "TEXT",
        "ai_explanation": "TEXT",
        "recommended_action": "TEXT",
        "assigned_department": "TEXT",
        "status": "TEXT DEFAULT 'OPEN'",
        "duplicate_of": "INTEGER",
        "emergency": "INTEGER DEFAULT 0",
        "photo_path": "TEXT",
        "created_at": "TEXT"
    }

    for column, definition in required_columns.items():
        if column not in columns:
            connection.execute(
                f"ALTER TABLE incidents ADD COLUMN {column} {definition}"
            )

    connection.commit()

    # Some earlier versions used `department` instead of
    # `assigned_department`. Preserve that information when present.
    columns = _table_columns(connection)
    if "department" in columns and "assigned_department" in columns:
        connection.execute("""
            UPDATE incidents
            SET assigned_department = department
            WHERE (assigned_department IS NULL OR assigned_department = '')
              AND department IS NOT NULL
        """)
        connection.commit()


def initialize_database():
    """Create the database if needed and safely migrate older versions."""

    connection = get_connection()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS incidents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            description TEXT,
            category TEXT,
            location TEXT,
            latitude REAL,
            longitude REAL,
            priority TEXT,
            risk_score INTEGER DEFAULT 0,
            risk_level TEXT,
            ai_explanation TEXT,
            recommended_action TEXT,
            assigned_department TEXT,
            status TEXT DEFAULT 'OPEN',
            duplicate_of INTEGER,
            emergency INTEGER DEFAULT 0,
            photo_path TEXT,
            created_at TEXT
        )
    """)

    connection.commit()
    _add_missing_columns(connection)

    # Fill timestamps for older rows that do not have one.
    connection.execute("""
        UPDATE incidents
        SET created_at = ?
        WHERE created_at IS NULL OR created_at = ''
    """, (datetime.now().isoformat(sep=" ", timespec="seconds"),))

    # Keep safe defaults for older records.
    connection.execute("""
        UPDATE incidents
        SET status = 'OPEN'
        WHERE status IS NULL OR status = ''
    """)

    connection.execute("""
        UPDATE incidents
        SET emergency = 0
        WHERE emergency IS NULL
    """)

    connection.commit()
    connection.close()


# ============================================================
# INCIDENT CRUD
# ============================================================

def add_incident(
    title,
    description,
    category,
    location,
    latitude=None,
    longitude=None,
    priority=None,
    risk_score=0,
    risk_level=None,
    ai_explanation=None,
    recommended_action=None,
    assigned_department=None,
    status="OPEN",
    duplicate_of=None,
    emergency=0,
    photo_path=None
):
    """Save an incident, including its optional photo path."""

    initialize_database()
    connection = get_connection()
    columns = _table_columns(connection)

    values = {
        "title": title,
        "description": description,
        "category": category,
        "location": location,
        "latitude": latitude,
        "longitude": longitude,
        "priority": priority,
        "risk_score": risk_score,
        "risk_level": risk_level,
        "ai_explanation": ai_explanation,
        "recommended_action": recommended_action,
        "assigned_department": assigned_department,
        "status": status,
        "duplicate_of": duplicate_of,
        "emergency": 1 if emergency else 0,
        "photo_path": photo_path,
        "created_at": datetime.now().isoformat(sep=" ", timespec="seconds")
    }

    # Only insert columns that actually exist. This keeps the function
    # compatible with an older SQLite database while migration is running.
    insert_values = {
        key: value
        for key, value in values.items()
        if key in columns
    }

    # Compatibility with an older schema that used `department`.
    if "assigned_department" not in columns and "department" in columns:
        insert_values["department"] = assigned_department
        insert_values.pop("assigned_department", None)

    column_names = list(insert_values.keys())
    placeholders = ", ".join("?" for _ in column_names)
    sql = f"""
        INSERT INTO incidents ({', '.join(column_names)})
        VALUES ({placeholders})
    """

    cursor = connection.execute(
        sql,
        [insert_values[column] for column in column_names]
    )

    incident_id = cursor.lastrowid
    connection.commit()
    connection.close()

    return incident_id


def get_all_incidents():
    initialize_database()
    connection = get_connection()

    rows = connection.execute("""
        SELECT *
        FROM incidents
        ORDER BY id DESC
    """).fetchall()

    connection.close()
    return [dict(row) for row in rows]


def get_incident(incident_id):
    initialize_database()
    connection = get_connection()

    row = connection.execute("""
        SELECT *
        FROM incidents
        WHERE id = ?
    """, (incident_id,)).fetchone()

    connection.close()
    return dict(row) if row else None


def update_incident_status(incident_id, status):
    initialize_database()
    connection = get_connection()

    connection.execute("""
        UPDATE incidents
        SET status = ?
        WHERE id = ?
    """, (status, incident_id))

    connection.commit()
    connection.close()


def update_incident_department(incident_id, department):
    initialize_database()
    connection = get_connection()
    columns = _table_columns(connection)

    if "assigned_department" in columns:
        connection.execute("""
            UPDATE incidents
            SET assigned_department = ?
            WHERE id = ?
        """, (department, incident_id))

    if "department" in columns:
        connection.execute("""
            UPDATE incidents
            SET department = ?
            WHERE id = ?
        """, (department, incident_id))

    connection.commit()
    connection.close()


def update_incident_photo(incident_id, photo_path):
    initialize_database()
    connection = get_connection()

    connection.execute("""
        UPDATE incidents
        SET photo_path = ?
        WHERE id = ?
    """, (photo_path, incident_id))

    connection.commit()
    connection.close()


# ============================================================
# DUPLICATE DETECTION
# ============================================================

def find_duplicate(category, location, description):
    initialize_database()
    connection = get_connection()

    # Prefer same category + same location. A description fragment is used
    # as an additional signal, but an exact description is not required.
    row = connection.execute("""
        SELECT *
        FROM incidents
        WHERE LOWER(COALESCE(category, '')) = LOWER(?)
          AND LOWER(COALESCE(location, '')) = LOWER(?)
        ORDER BY id DESC
        LIMIT 1
    """, (category, location)).fetchone()

    connection.close()
    return dict(row) if row else None


# ============================================================
# STATISTICS
# ============================================================

def get_incident_statistics():
    initialize_database()
    connection = get_connection()

    total = connection.execute(
        "SELECT COUNT(*) FROM incidents"
    ).fetchone()[0]

    open_count = connection.execute(
        "SELECT COUNT(*) FROM incidents WHERE status = 'OPEN'"
    ).fetchone()[0]

    assigned_count = connection.execute(
        "SELECT COUNT(*) FROM incidents WHERE status = 'ASSIGNED'"
    ).fetchone()[0]

    in_progress = connection.execute(
        "SELECT COUNT(*) FROM incidents WHERE status = 'IN PROGRESS'"
    ).fetchone()[0]

    resolved = connection.execute(
        "SELECT COUNT(*) FROM incidents WHERE status = 'RESOLVED'"
    ).fetchone()[0]

    critical = connection.execute(
        "SELECT COUNT(*) FROM incidents WHERE risk_level = 'CRITICAL'"
    ).fetchone()[0]

    high = connection.execute(
        "SELECT COUNT(*) FROM incidents WHERE risk_level = 'HIGH'"
    ).fetchone()[0]

    emergency = connection.execute(
        "SELECT COUNT(*) FROM incidents WHERE emergency = 1"
    ).fetchone()[0]

    connection.close()

    return {
        "total": total,
        "open": open_count,
        "assigned": assigned_count,
        "in_progress": in_progress,
        "resolved": resolved,
        "critical": critical,
        "high": high,
        "emergency": emergency
    }


# ============================================================
# STARTUP
# ============================================================
# ============================================================
# DEMO: SPREAD EXISTING INCIDENTS ON THE MAP
# ============================================================

def spread_demo_incident_locations():
    connection = get_connection()

    # Different locations around the campus area
    locations = [
        (13.0676204, 77.5019042),
        (13.0691204, 77.5032042),
        (13.0659204, 77.5045042),
        (13.0710204, 77.5006042),
        (13.0645204, 77.4992042),
        (13.0684204, 77.5070042),
        (13.0629204, 77.5028042),
        (13.0702204, 77.5061042),
        (13.0661204, 77.4980042),
        (13.0720204, 77.5040042),
        (13.0638204, 77.5062042),
        (13.0698204, 77.4996042),
        (13.0619204, 77.5004042),
    ]

    rows = connection.execute(
        "SELECT rowid FROM incidents ORDER BY rowid"
    ).fetchall()

    for index, row in enumerate(rows):
        if index >= len(locations):
            break

        latitude, longitude = locations[index]

        connection.execute(
            """
            UPDATE incidents
            SET latitude = ?,
                longitude = ?
            WHERE rowid = ?
            """,
            (latitude, longitude, row["rowid"])
        )

    connection.commit()
    connection.close()

    print("Incident locations updated successfully.")

if __name__ == "__main__":
    initialize_database()
    spread_demo_incident_locations()
