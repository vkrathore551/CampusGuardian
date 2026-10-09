import sqlite3
import hashlib
import secrets
from datetime import datetime
from pathlib import Path


# ============================================================
# DATABASE CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
DB_NAME = str(BASE_DIR / "campusguardian.db")


def get_connection():
    connection = sqlite3.connect(DB_NAME)
    connection.row_factory = sqlite3.Row
    return connection


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ============================================================
# PASSWORD SECURITY
# ============================================================

def hash_password(password, salt=None):
    salt = salt or secrets.token_hex(16)

    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        120000,
    ).hex()

    return f"{salt}${digest}"


def verify_password(password, stored_password):
    if not stored_password or not password:
        return False
    try:
        if "$" in stored_password:
            salt, digest = stored_password.split("$", 1)
            check = hashlib.pbkdf2_hmac(
                "sha256",
                password.encode("utf-8"),
                salt.encode("utf-8"),
                120000,
            ).hex()
            return secrets.compare_digest(check, digest)
        # Fallback to legacy raw SHA-256
        legacy_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
        return secrets.compare_digest(legacy_hash, stored_password)
    except Exception:
        return False


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def initialize_database():

    connection = get_connection()

    # --------------------------------------------------------
    # USERS
    # --------------------------------------------------------

    connection.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            department TEXT DEFAULT '',
            phone TEXT DEFAULT '',
            created_at TEXT NOT NULL
        )
    """)

    # --------------------------------------------------------
    # INCIDENTS
    # --------------------------------------------------------

    connection.execute("""
        CREATE TABLE IF NOT EXISTS incidents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER,

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

            admin_note TEXT DEFAULT '',

            created_at TEXT,

            FOREIGN KEY(user_id)
                REFERENCES users(id)
        )
    """)

    # --------------------------------------------------------
    # NOTIFICATIONS
    # --------------------------------------------------------

    connection.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            notification_type TEXT DEFAULT 'info',
            is_read INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            FOREIGN KEY(user_id)
                REFERENCES users(id)
        )
    """)

    connection.commit()

    # ========================================================
    # MIGRATE OLD DATABASES
    # ========================================================

    incident_columns = {
        row["name"]
        for row in connection.execute(
            "PRAGMA table_info(incidents)"
        ).fetchall()
    }

    missing_incident_columns = {
        "user_id": "INTEGER",
        "title": "TEXT",
        "description": "TEXT",
        "category": "TEXT",
        "location": "TEXT",
        "latitude": "REAL",
        "longitude": "REAL",
        "priority": "TEXT",
        "risk_score": "INTEGER DEFAULT 0",
        "risk": "TEXT",
        "risk_level": "TEXT",
        "ai_why": "TEXT",
        "ai_explanation": "TEXT",
        "recommended_action": "TEXT",
        "department": "TEXT",
        "assigned_department": "TEXT",
        "status": "TEXT DEFAULT 'OPEN'",
        "duplicate_of": "INTEGER",
        "emergency": "INTEGER DEFAULT 0",
        "photo_path": "TEXT",
        "admin_note": "TEXT DEFAULT ''",
        "created_at": "TEXT",
    }

    for column, definition in missing_incident_columns.items():

        if column not in incident_columns:

            connection.execute(
                f"ALTER TABLE incidents ADD COLUMN {column} {definition}"
            )

    # --------------------------------------------------------
    # USER MIGRATION
    # --------------------------------------------------------

    user_columns = {
        row["name"]
        for row in connection.execute(
            "PRAGMA table_info(users)"
        ).fetchall()
    }

    missing_user_columns = {
        "department": "TEXT DEFAULT ''",
        "phone": "TEXT DEFAULT ''",
        "created_at": "TEXT",
    }

    for column, definition in missing_user_columns.items():

        if column not in user_columns:

            connection.execute(
                f"ALTER TABLE users ADD COLUMN {column} {definition}"
            )

    # --------------------------------------------------------
    # DEFAULT VALUES FOR OLD INCIDENTS
    # --------------------------------------------------------

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

    connection.execute("""
        UPDATE incidents
        SET risk_score = 0
        WHERE risk_score IS NULL
    """)

    connection.execute("""
        UPDATE incidents
        SET created_at = ?
        WHERE created_at IS NULL OR created_at = ''
    """, (now(),))

    # Synchronize dual column representations across schemas
    connection.execute("""
        UPDATE incidents
        SET risk_level = COALESCE(NULLIF(risk_level, ''), risk),
            risk = COALESCE(NULLIF(risk, ''), risk_level),
            assigned_department = COALESCE(NULLIF(assigned_department, ''), department),
            department = COALESCE(NULLIF(department, ''), assigned_department),
            ai_explanation = COALESCE(NULLIF(ai_explanation, ''), ai_why),
            ai_why = COALESCE(NULLIF(ai_why, ''), ai_explanation),
            priority = COALESCE(NULLIF(priority, ''), 'Normal')
    """)

    # --------------------------------------------------------
    # CREATE DEMO ACCOUNTS
    # --------------------------------------------------------

    user_count = connection.execute(
        "SELECT COUNT(*) FROM users"
    ).fetchone()[0]

    if user_count == 0:

        connection.execute("""
            INSERT INTO users
            (
                name,
                email,
                password,
                role,
                department,
                phone,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            "Demo Student",
            "student@campusguardian.com",
            hash_password("student123"),
            "user",
            "Computer Science",
            "+91 9876543210",
            now(),
        ))

        connection.execute("""
            INSERT INTO users
            (
                name,
                email,
                password,
                role,
                department,
                phone,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            "Campus Administrator",
            "admin@campusguardian.com",
            hash_password("admin123"),
            "admin",
            "Campus Security",
            "+91 9876543211",
            now(),
        ))

    connection.commit()

    # --------------------------------------------------------
    # ASSIGN OLD INCIDENTS TO DEMO STUDENT
    # --------------------------------------------------------

    student = connection.execute("""
        SELECT id
        FROM users
        WHERE role = 'user'
        ORDER BY id
        LIMIT 1
    """).fetchone()

    if student:

        connection.execute("""
            UPDATE incidents
            SET user_id = ?
            WHERE user_id IS NULL
        """, (student["id"],))

    connection.commit()
    connection.close()


# ============================================================
# USER FUNCTIONS
# ============================================================

def get_user(user_id):

    initialize_database()

    connection = get_connection()

    row = connection.execute("""
        SELECT *
        FROM users
        WHERE id = ?
    """, (user_id,)).fetchone()

    connection.close()

    return dict(row) if row else None


def get_user_by_email(email):

    initialize_database()

    connection = get_connection()

    row = connection.execute("""
        SELECT *
        FROM users
        WHERE LOWER(email) = LOWER(?)
    """, (email.strip(),)).fetchone()

    connection.close()

    return dict(row) if row else None


def authenticate_user(email, password):

    user = get_user_by_email(email)

    if not user:
        return None

    if verify_password(password, user["password"]):
        return user

    return None


def get_all_users():

    initialize_database()

    connection = get_connection()

    rows = connection.execute("""
        SELECT
            id,
            name,
            email,
            role,
            department,
            phone,
            created_at
        FROM users
        ORDER BY id DESC
    """).fetchall()

    connection.close()

    return [dict(row) for row in rows]


def create_user(
    name,
    email,
    password,
    role="user",
    department="",
    phone=""
):

    initialize_database()

    connection = get_connection()

    try:

        cursor = connection.execute("""
            INSERT INTO users
            (
                name,
                email,
                password,
                role,
                department,
                phone,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            name,
            email,
            hash_password(password),
            role,
            department,
            phone,
            now(),
        ))

        user_id = cursor.lastrowid

        connection.commit()

        return user_id

    except sqlite3.IntegrityError:

        connection.rollback()

        return None

    finally:

        connection.close()


# ============================================================
# INCIDENT FUNCTIONS
# ============================================================

def add_incident(
    title,
    description,
    category,
    location,
    latitude=None,
    longitude=None,
    priority="Normal",
    risk_score=0,
    risk_level="LOW",
    ai_explanation="",
    recommended_action="",
    assigned_department="Campus Security",
    status="OPEN",
    duplicate_of=None,
    emergency=0,
    photo_path=None,
    user_id=None,
):

    initialize_database()

    connection = get_connection()

    cursor = connection.execute("""
        INSERT INTO incidents
        (
            user_id,
            title,
            description,
            category,
            location,
            latitude,
            longitude,
            priority,
            risk_score,
            risk,
            risk_level,
            ai_why,
            ai_explanation,
            recommended_action,
            department,
            assigned_department,
            status,
            duplicate_of,
            emergency,
            photo_path,
            admin_note,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        title,
        description,
        category,
        location,
        latitude,
        longitude,
        priority,
        risk_score,
        risk_level,
        risk_level,
        ai_explanation,
        ai_explanation,
        recommended_action,
        assigned_department,
        assigned_department,
        status,
        duplicate_of,
        1 if emergency else 0,
        photo_path,
        "",
        now(),
    ))

    incident_id = cursor.lastrowid

    connection.commit()
    connection.close()

    return incident_id


def get_all_incidents():

    initialize_database()

    connection = get_connection()

    rows = connection.execute("""
        SELECT
            i.*,
            u.name AS reporter_name,
            u.email AS reporter_email
        FROM incidents i
        LEFT JOIN users u
            ON i.user_id = u.id
        ORDER BY i.id DESC
    """).fetchall()

    connection.close()

    return [dict(row) for row in rows]


def get_incident(incident_id):

    initialize_database()

    connection = get_connection()

    row = connection.execute("""
        SELECT
            i.*,
            u.name AS reporter_name,
            u.email AS reporter_email
        FROM incidents i
        LEFT JOIN users u
            ON i.user_id = u.id
        WHERE i.id = ?
    """, (incident_id,)).fetchone()

    connection.close()

    return dict(row) if row else None


def get_user_incidents(user_id):

    initialize_database()

    connection = get_connection()

    rows = connection.execute("""
        SELECT *
        FROM incidents
        WHERE user_id = ?
        ORDER BY id DESC
    """, (user_id,)).fetchall()

    connection.close()

    return [dict(row) for row in rows]


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


def update_incident_department(
    incident_id,
    department
):

    initialize_database()

    connection = get_connection()

    connection.execute("""
        UPDATE incidents
        SET department = ?, assigned_department = ?
        WHERE id = ?
    """, (department, department, incident_id))

    connection.commit()
    connection.close()


def update_incident_admin_note(
    incident_id,
    note
):

    initialize_database()

    connection = get_connection()

    connection.execute("""
        UPDATE incidents
        SET admin_note = ?
        WHERE id = ?
    """, (note, incident_id))

    connection.commit()
    connection.close()


def find_duplicate(
    category,
    location,
    description=""
):

    initialize_database()

    connection = get_connection()

    row = connection.execute("""
        SELECT *
        FROM incidents
        WHERE LOWER(COALESCE(category, '')) = LOWER(?)
        AND LOWER(COALESCE(location, '')) = LOWER(?)
        ORDER BY id DESC
        LIMIT 1
    """, (
        category,
        location
    )).fetchone()

    connection.close()

    return dict(row) if row else None


# ============================================================
# NOTIFICATIONS
# ============================================================

def add_notification(
    user_id,
    message,
    notification_type="info"
):

    initialize_database()

    connection = get_connection()

    connection.execute("""
        INSERT INTO notifications
        (
            user_id,
            message,
            notification_type,
            is_read,
            created_at
        )
        VALUES (?, ?, ?, 0, ?)
    """, (
        user_id,
        message,
        notification_type,
        now(),
    ))

    connection.commit()
    connection.close()


def get_notifications(user_id):

    initialize_database()

    connection = get_connection()

    rows = connection.execute("""
        SELECT *
        FROM notifications
        WHERE user_id = ?
        ORDER BY id DESC
    """, (user_id,)).fetchall()

    connection.close()

    return [dict(row) for row in rows]


def get_unread_notification_count(user_id):

    initialize_database()

    connection = get_connection()

    count = connection.execute("""
        SELECT COUNT(*)
        FROM notifications
        WHERE user_id = ?
        AND is_read = 0
    """, (user_id,)).fetchone()[0]

    connection.close()

    return count


def mark_notifications_read(user_id):

    initialize_database()

    connection = get_connection()

    connection.execute("""
        UPDATE notifications
        SET is_read = 1
        WHERE user_id = ?
    """, (user_id,))

    connection.commit()
    connection.close()


# ============================================================
# STATISTICS
# ============================================================

def get_incident_statistics():

    incidents = get_all_incidents()

    total = len(incidents)

    open_count = sum(
        1 for x in incidents
        if str(x.get("status", "")).upper() == "OPEN"
    )

    assigned = sum(
        1 for x in incidents
        if str(x.get("status", "")).upper() == "ASSIGNED"
    )

    in_progress = sum(
        1 for x in incidents
        if str(x.get("status", "")).upper()
        == "IN PROGRESS"
    )

    resolved = sum(
        1 for x in incidents
        if str(x.get("status", "")).upper()
        == "RESOLVED"
    )

    critical = sum(
        1 for x in incidents
        if str(x.get("risk_level", "")).upper()
        == "CRITICAL"
    )

    high = sum(
        1 for x in incidents
        if str(x.get("risk_level", "")).upper()
        == "HIGH"
    )

    emergency = sum(
        1 for x in incidents
        if x.get("emergency") == 1
    )

    return {
        "total": total,
        "open": open_count,
        "assigned": assigned,
        "in_progress": in_progress,
        "resolved": resolved,
        "critical": critical,
        "high": high,
        "emergency": emergency,
    }


# ============================================================
# INITIALIZE
# ============================================================

initialize_database()