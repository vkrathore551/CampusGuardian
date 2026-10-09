import streamlit as st
import sqlite3
import hashlib
import secrets
import re
from datetime import datetime
from pathlib import Path
import io
from PIL import Image
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ============================================================
# CONFIGURATION & CONSTANTS
# ============================================================

st.set_page_config(
    page_title="CampusGuardian AI",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

BASE_DIR = Path(__file__).resolve().parent
DB_NAME = str(BASE_DIR / "campusguardian.db")
PHOTO_FOLDER = BASE_DIR / "incident_photos"
PHOTO_FOLDER.mkdir(parents=True, exist_ok=True)

# Sapthagiri NPS University reference campus coordinates
CAMPUS_NAME = "Sapthagiri NPS University"
CAMPUS_ADDRESS = "#14/5, Chikkasandra, Hesarghatta Main Road, Bengaluru, Karnataka 560057"
CAMPUS_LATITUDE = 13.069473
CAMPUS_LONGITUDE = 77.502191


# ============================================================
# GLOBAL CSS DESIGN SYSTEM
# ============================================================

def inject_custom_css():
    """Inject modern, responsive styling across the entire application."""
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

        html, body, [class*="css"] {
            font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
        }

        /* App Background */
        [data-testid="stAppViewContainer"] {
            background:
                radial-gradient(circle at 10% 12%, rgba(37,99,235,0.18), transparent 30%),
                radial-gradient(circle at 90% 88%, rgba(6,182,212,0.12), transparent 30%),
                #070f1e !important;
            color: #f1f5f9;
        }

        [data-testid="stHeader"] {
            background: rgba(7, 15, 30, 0.75) !important;
            backdrop-filter: blur(12px);
        }

        /* Sidebar Styling */
        [data-testid="stSidebar"] {
            background: #091326 !important;
            border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
        }

        /* Metric Cards - unclipped labels and values */
        [data-testid="stMetric"] {
            background: rgba(15, 25, 46, 0.75) !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            border-radius: 14px !important;
            padding: 14px 18px !important;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25) !important;
            transition: all 0.2s ease;
            min-height: 94px !important;
            display: flex !important;
            flex-direction: column !important;
            justify-content: center !important;
        }

        [data-testid="stMetric"]:hover {
            border-color: rgba(6, 182, 212, 0.4) !important;
            transform: translateY(-2px);
        }

        [data-testid="stMetricLabel"] {
            font-size: 11.5px !important;
            font-weight: 700 !important;
            color: #94a3b8 !important;
            text-transform: uppercase !important;
            letter-spacing: 0.5px !important;
            white-space: normal !important;
            word-break: break-word !important;
            line-height: 1.3 !important;
            overflow: visible !important;
        }

        [data-testid="stMetricValue"] {
            font-size: clamp(20px, 2.2vw, 28px) !important;
            font-weight: 800 !important;
            color: #f8fafc !important;
            line-height: 1.2 !important;
        }

        /* Custom Card Elements */
        .cg-card {
            background: rgba(15, 25, 46, 0.65);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 14px;
            padding: 18px 20px;
            margin-bottom: 16px;
            backdrop-filter: blur(8px);
            transition: border-color 0.2s ease, box-shadow 0.2s ease;
        }

        .cg-card:hover {
            border-color: rgba(56, 189, 248, 0.3);
            box-shadow: 0 6px 24px rgba(0, 0, 0, 0.3);
        }

        .cg-card-header {
            font-size: 17px;
            font-weight: 700;
            color: #f8fafc;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        /* Badges */
        .cg-badge {
            display: inline-flex;
            align-items: center;
            gap: 4px;
            padding: 3px 10px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 0.3px;
            white-space: nowrap;
        }

        .badge-critical { background: rgba(239, 68, 68, 0.18); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.4); }
        .badge-high { background: rgba(249, 115, 22, 0.18); color: #fb923c; border: 1px solid rgba(249, 115, 22, 0.4); }
        .badge-medium { background: rgba(234, 179, 8, 0.18); color: #facc15; border: 1px solid rgba(234, 179, 8, 0.4); }
        .badge-low { background: rgba(34, 197, 94, 0.18); color: #4ade80; border: 1px solid rgba(34, 197, 94, 0.4); }

        .badge-urgent { background: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.45); }
        .badge-normal { background: rgba(59, 130, 246, 0.2); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.45); }

        .badge-open { background: rgba(59, 130, 246, 0.18); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.4); }
        .badge-assigned { background: rgba(168, 85, 247, 0.18); color: #c084fc; border: 1px solid rgba(168, 85, 247, 0.4); }
        .badge-in-progress { background: rgba(245, 158, 11, 0.18); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.4); }
        .badge-resolved { background: rgba(16, 185, 129, 0.18); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.4); }

        /* Status Timeline Progress */
        .tracker-container {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin: 14px 0 6px 0;
            padding: 12px 16px;
            background: rgba(11, 20, 38, 0.65);
            border-radius: 10px;
            border: 1px solid rgba(255, 255, 255, 0.06);
            overflow-x: auto;
        }

        .tracker-step {
            display: flex;
            flex-direction: column;
            align-items: center;
            font-size: 11px;
            font-weight: 600;
            min-width: 72px;
            text-align: center;
        }

        .tracker-step.active { color: #38bdf8; font-weight: 700; }
        .tracker-step.completed { color: #34d399; }
        .tracker-step.pending { color: #64748b; }

        .tracker-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            margin-bottom: 5px;
            display: inline-block;
        }

        .dot-completed {
            background: #10b981;
            box-shadow: 0 0 8px rgba(16, 185, 129, 0.6);
        }

        .dot-active {
            background: #38bdf8;
            box-shadow: 0 0 8px rgba(56, 189, 248, 0.6);
        }

        .dot-pending {
            background: #475569;
        }

        .tracker-line {
            flex: 1;
            height: 2px;
            background: rgba(255, 255, 255, 0.1);
            margin: 0 8px;
            min-width: 24px;
        }

        .tracker-line.active { background: #34d399; }

        /* Form Inputs */
        div[data-baseweb="input"] {
            background: #0d182b !important;
            border: 1px solid #23354f !important;
            border-radius: 10px !important;
        }

        div[data-baseweb="input"] input {
            color: #f8fafc !important;
        }

        div[data-baseweb="textarea"] textarea {
            color: #f8fafc !important;
            background: #0d182b !important;
        }

        div[data-baseweb="select"] {
            background: #0d182b !important;
            border-radius: 10px !important;
        }

        /* Expanders */
        [data-testid="stExpander"] {
            background: rgba(15, 25, 46, 0.5) !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            border-radius: 12px !important;
            margin-bottom: 10px !important;
        }

        /* Buttons */
        .stButton > button {
            border-radius: 10px !important;
            font-weight: 700 !important;
            letter-spacing: 0.3px !important;
            transition: all 0.2s ease !important;
        }

        /* Quick action pill cards */
        .action-card {
            background: rgba(15, 25, 46, 0.7);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 12px;
            padding: 16px;
            text-align: center;
            transition: all 0.2s ease;
        }

        .action-card:hover {
            border-color: rgba(6, 182, 212, 0.5);
            background: rgba(15, 25, 46, 0.9);
        }

        @media (max-width: 768px) {
            .block-container {
                padding-left: 1rem !important;
                padding-right: 1rem !important;
            }
            .tracker-container {
                overflow-x: scroll;
            }
        }
    </style>
    """, unsafe_allow_html=True)


# ============================================================
# PHOTO STORAGE & RESOLUTION
# ============================================================

def resolve_incident_photo(photo_value):
    """Reliably resolve an incident photo across platforms and working directories."""
    if not photo_value:
        return None
    raw = Path(str(photo_value).strip().replace("\\", "/"))
    candidates = [
        raw,
        BASE_DIR / raw,
        Path.cwd() / raw,
        PHOTO_FOLDER / raw.name,
        BASE_DIR / "incident_photos" / raw.name,
        Path.cwd() / "incident_photos" / raw.name,
    ]
    seen = set()
    for candidate in candidates:
        try:
            resolved = candidate.resolve()
        except OSError:
            continue
        key = str(resolved).lower()
        if key in seen:
            continue
        seen.add(key)
        if resolved.exists() and resolved.is_file():
            return resolved
    return None


# ============================================================
# DATABASE & AUTHENTICATION
# ============================================================

def get_connection():
    connection = sqlite3.connect(DB_NAME)
    connection.row_factory = sqlite3.Row
    return connection


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
        # Fallback to legacy raw SHA-256 for backward compatibility
        legacy_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
        return secrets.compare_digest(legacy_hash, stored_password)
    except Exception:
        return False


def initialize_database():
    """Create tables and verify columns for CampusGuardian SQLite database."""
    connection = get_connection()
    try:
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

        connection.execute("""
            CREATE TABLE IF NOT EXISTS incidents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                description TEXT NOT NULL,
                location TEXT NOT NULL,
                latitude REAL DEFAULT 0,
                longitude REAL DEFAULT 0,
                risk TEXT DEFAULT 'Low',
                risk_score INTEGER DEFAULT 0,
                priority TEXT DEFAULT 'Normal',
                status TEXT DEFAULT 'Open',
                department TEXT DEFAULT 'Campus Security',
                ai_why TEXT DEFAULT '',
                recommended_action TEXT DEFAULT '',
                photo_path TEXT DEFAULT '',
                admin_note TEXT DEFAULT '',
                emergency INTEGER DEFAULT 0,
                is_demo INTEGER DEFAULT 0,
                duplicate_of INTEGER,
                created_at TEXT NOT NULL
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                message TEXT NOT NULL,
                is_read INTEGER DEFAULT 0,
                created_at TEXT NOT NULL
            )
        """)

        # Migration column checks
        def columns(table_name):
            return {row["name"] for row in connection.execute(f"PRAGMA table_info({table_name})").fetchall()}

        def add_col(table_name, col_name, col_def):
            if col_name not in columns(table_name):
                connection.execute(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_def}")

        for col, defn in [
            ("risk_score", "INTEGER DEFAULT 0"),
            ("priority", "TEXT DEFAULT 'Normal'"),
            ("recommended_action", "TEXT DEFAULT ''"),
            ("duplicate_of", "INTEGER"),
            ("emergency", "INTEGER DEFAULT 0"),
            ("is_demo", "INTEGER DEFAULT 0"),
            ("admin_note", "TEXT DEFAULT ''"),
            ("ai_why", "TEXT DEFAULT ''"),
            ("risk", "TEXT DEFAULT 'Low'"),
            ("risk_level", "TEXT DEFAULT ''"),
            ("department", "TEXT DEFAULT 'Campus Security'"),
            ("assigned_department", "TEXT DEFAULT ''"),
            ("ai_explanation", "TEXT DEFAULT ''"),
        ]:
            add_col("incidents", col, defn)

        # Synchronize dual column representations across schemas safely
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

        # Notifications migration check
        if "is_read" not in columns("notifications"):
            connection.execute("ALTER TABLE notifications ADD COLUMN is_read INTEGER DEFAULT 0")
            if "read" in columns("notifications"):
                connection.execute("UPDATE notifications SET is_read = COALESCE(read, 0)")

        # Default demo accounts
        count = connection.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        if count == 0:
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            connection.execute("""
                INSERT INTO users (name, email, password, role, department, phone, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, ("Demo Student", "student@campusguardian.com", hash_password("student123"), "user", "Computer Science", "+91 9876543210", now_str))
            connection.execute("""
                INSERT INTO users (name, email, password, role, department, phone, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, ("Campus Administrator", "admin@campusguardian.com", hash_password("admin123"), "admin", "Campus Security", "+91 9876543211", now_str))

        connection.commit()
    finally:
        connection.close()


def login_user(email, password):
    connection = get_connection()
    user = connection.execute(
        "SELECT * FROM users WHERE lower(email)=lower(?)",
        (email.strip(),)
    ).fetchone()
    if user is None:
        connection.close()
        return None

    if verify_password(password, user["password"]):
        user_dict = dict(user)
        # Transparently upgrade legacy SHA-256 hash to PBKDF2
        if "$" not in user["password"]:
            try:
                new_hash = hash_password(password)
                connection.execute(
                    "UPDATE users SET password = ? WHERE id = ?",
                    (new_hash, user["id"])
                )
                connection.commit()
                user_dict["password"] = new_hash
            except sqlite3.Error:
                pass
        connection.close()
        return user_dict

    connection.close()
    return None


def create_account(name, email, password, department="", phone=""):
    if not name or not email or not password:
        return False, "Please fill in all required fields."
    if len(password) < 6:
        return False, "Password must contain at least 6 characters."

    try:
        connection = get_connection()
        connection.execute("""
            INSERT INTO users (name, email, password, role, department, phone, created_at)
            VALUES (?, ?, ?, 'user', ?, ?, ?)
        """, (
            name.strip(),
            email.strip().lower(),
            hash_password(password),
            department.strip(),
            phone.strip(),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))
        connection.commit()
        connection.close()
        return True, "Account created successfully! You can now sign in."
    except sqlite3.IntegrityError:
        return False, "An account with this email address already exists."


# ============================================================
# AI RISK SCORING & INTELLIGENCE
# ============================================================

def calculate_risk(category, description):
    text = (str(category) + " " + str(description)).lower()

    critical_keywords = [
        "fire", "explosion", "gas leak", "attack", "weapon", "gun",
        "knife", "unconscious", "collapse", "hostage", "smoke pouring"
    ]
    for word in critical_keywords:
        if word in text:
            return "Critical"

    high_keywords = [
        "harassment", "assault", "fight", "fighting", "blood",
        "injury", "injured", "lift stuck", "elevator stuck", "trapped",
        "spark", "electric shock", "exposed wire", "threat"
    ]
    for word in high_keywords:
        if word in text:
            return "High"

    medium_keywords = [
        "water leak", "leakage", "pipe burst", "flooding", "pothole",
        "streetlight broken", "dark area", "broken glass", "lock broken"
    ]
    for word in medium_keywords:
        if word in text:
            return "Medium"

    return "Low"


def explain_risk(risk):
    explanations = {
        "Critical": "🚨 Life-safety threat requiring immediate emergency evacuation or security intervention.",
        "High": "⚠️ High-severity issue with immediate safety hazard, physical harm, or vital system failure.",
        "Medium": "🟡 Infrastructure or maintenance issue requiring timely inspection to prevent safety degradation.",
        "Low": "🟢 Routine observation or non-hazardous maintenance request."
    }
    return explanations.get(risk, "Campus safety event under administrative monitoring.")


def assign_department(category):
    category_map = {
        "Fire": "Fire & Safety",
        "Medical Emergency": "Medical Unit",
        "Lift": "Lift & Elevator Maintenance",
        "Lift/Elevator": "Lift & Elevator Maintenance",
        "Water Leakage": "Maintenance",
        "Infrastructure": "Maintenance",
        "Pothole": "Maintenance",
        "Streetlight": "Electrical Maintenance",
        "Security": "Campus Security",
        "Security Threat": "Campus Security",
        "Fighting": "Campus Security",
        "Harassment": "Student Welfare",
        "Traffic": "Campus Traffic",
    }
    return category_map.get(category, "Campus Security")


def calculate_campus_safety_score(df):
    """Calculate an operational 0-100 safety health score."""
    if df is None or df.empty:
        return 100
    total = len(df)
    active = int((df["status"] != "Resolved").sum())
    high = int(df["risk"].isin(["High", "Critical"]).sum())
    critical = int((df["risk"] == "Critical").sum())
    created = pd.to_datetime(df["created_at"], errors="coerce")
    recent = int((created >= pd.Timestamp.now() - pd.Timedelta(days=7)).sum())
    resolved = int((df["status"] == "Resolved").sum())

    score = 100.0
    score -= min(30, high * 5)
    score -= min(25, critical * 6)
    score -= min(20, active * 1.5)
    score -= min(15, recent * 1.0)
    score += min(10, (resolved / max(total, 1)) * 10)
    return int(max(0, min(100, round(score))))


def safety_score_label(score):
    if score >= 85:
        return "🟢 Optimal Safety", "Campus security operations are normal with low hazard concentration."
    if score >= 70:
        return "🟡 Moderate Watch", "Active reports are manageable; maintenance follow-up recommended."
    if score >= 50:
        return "🟠 Elevated Risk", "Multiple high-priority reports require expedited administrative action."
    return "🔴 Urgent Attention", "Critical safety threats detected. Deploy rapid response teams immediately."


def generate_safety_insight(df):
    if df is None or df.empty:
        return "No incident history available yet. Submit incident reports to activate AI trend insights."
    created = pd.to_datetime(df["created_at"], errors="coerce")
    now = pd.Timestamp.now()
    last7 = int((created >= now - pd.Timedelta(days=7)).sum())
    high = int(df["risk"].isin(["High", "Critical"]).sum())
    unresolved = int((df["status"] != "Resolved").sum())
    loc_counts = df["location"].astype(str).value_counts()
    top_loc = loc_counts.index[0] if not loc_counts.empty else "Campus Grounds"
    top_cnt = loc_counts.iloc[0] if not loc_counts.empty else 0

    return (
        f"In the past 7 days, **{last7} incident(s)** were recorded. The primary concentration point is **{top_loc}** "
        f"with {top_cnt} report(s). Currently **{high} high/critical** and **{unresolved} total unresolved** issue(s) "
        f"are open. Dispatching teams to top clusters significantly improves overall campus safety health."
    )


# ============================================================
# INCIDENT & NOTIFICATION DATA ACCESS
# ============================================================

def get_all_incidents():
    connection = get_connection()
    incidents = connection.execute("""
        SELECT
            incidents.*,
            COALESCE(users.name, 'Unknown Reporter') AS reporter,
            COALESCE(users.email, '') AS reporter_email
        FROM incidents
        LEFT JOIN users ON incidents.user_id = users.id
        ORDER BY incidents.id DESC
    """).fetchall()
    connection.close()
    return [dict(row) for row in incidents]


def get_user_incidents(user_id):
    connection = get_connection()
    incidents = connection.execute("""
        SELECT *
        FROM incidents
        WHERE user_id = ?
        ORDER BY id DESC
    """, (user_id,)).fetchall()
    connection.close()
    return [dict(row) for row in incidents]


def add_notification(user_id, message):
    connection = get_connection()
    try:
        connection.execute("""
            INSERT INTO notifications (user_id, message, is_read, created_at)
            VALUES (?, ?, 0, ?)
        """, (user_id, message, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        connection.commit()
    finally:
        connection.close()


def notify_admins(message):
    connection = get_connection()
    try:
        admins = connection.execute("SELECT id FROM users WHERE role = 'admin'").fetchall()
        for admin in admins:
            connection.execute("""
                INSERT INTO notifications (user_id, message, is_read, created_at)
                VALUES (?, ?, 0, ?)
            """, (admin["id"], message, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        connection.commit()
    finally:
        connection.close()


def get_notifications(user_id):
    connection = get_connection()
    rows = connection.execute("""
        SELECT * FROM notifications
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT 50
    """, (user_id,)).fetchall()
    connection.close()
    return [dict(row) for row in rows]


def get_unread_notification_count(user_id):
    connection = get_connection()
    cnt = connection.execute("""
        SELECT COUNT(*) FROM notifications
        WHERE user_id = ? AND is_read = 0
    """, (user_id,)).fetchone()[0]
    connection.close()
    return cnt


def mark_notifications_read(user_id):
    connection = get_connection()
    connection.execute("""
        UPDATE notifications SET is_read = 1
        WHERE user_id = ?
    """, (user_id,))
    connection.commit()
    connection.close()


# ============================================================
# MAPS & VISUALIZATIONS
# ============================================================

def render_campus_heatmap(df, title="🔥 Campus Safety Heatmap"):
    """Render a Plotly density heatmap with an OpenStreetMap base."""
    if df is None or df.empty:
        st.info("No mapped incidents are available for the heatmap.")
        return
    work = df.copy()
    for col in ["latitude", "longitude"]:
        if col not in work.columns:
            work[col] = pd.NA
        work[col] = pd.to_numeric(work[col], errors="coerce")

    work = work.dropna(subset=["latitude", "longitude"]).copy()
    work = work[
        work["latitude"].between(-90, 90)
        & work["longitude"].between(-180, 180)
        & ~((work["latitude"] == 0) & (work["longitude"] == 0))
    ]
    if work.empty:
        st.info("No valid GPS coordinates are available for the heatmap.")
        return

    weights = {"Critical": 5, "High": 4, "Medium": 2, "Low": 1}
    work["weight"] = work["risk"].map(weights).fillna(1)

    try:
        fig = go.Figure(go.Densitymapbox(
            lat=work["latitude"],
            lon=work["longitude"],
            z=work["weight"],
            radius=26,
            colorscale="Turbo",
            showscale=True,
            colorbar=dict(title="Risk Weight")
        ))
        fig.update_layout(
            title=title,
            mapbox=dict(
                style="open-street-map",
                center={"lat": CAMPUS_LATITUDE, "lon": CAMPUS_LONGITUDE},
                zoom=14
            ),
            height=480,
            margin=dict(l=0, r=0, t=50, b=0)
        )
        st.plotly_chart(fig, use_container_width=True)
    except Exception:
        st.map(work[["latitude", "longitude"]], use_container_width=True)


# ============================================================
# LOGIN & REGISTRATION PAGE
# ============================================================

def login_page():
    inject_custom_css()

    brand_col1, brand_col2 = st.columns([0.08, 0.92])
    with brand_col1:
        st.markdown("## 🛡️")
    with brand_col2:
        st.markdown('<h2 style="margin:0;color:#f8fafc;font-weight:800;">CampusGuardian AI</h2>', unsafe_allow_html=True)
        st.caption("INTELLIGENT CAMPUS SAFETY & RAPID INCIDENT TRIAGE PLATFORM")

    left, right = st.columns([1.15, 0.85], gap="large")

    with left:
        st.markdown('<div style="color:#38bdf8;font-size:12px;font-weight:800;letter-spacing:1px;margin-top:20px;">AI-POWERED PREVENTIVE SAFETY</div>', unsafe_allow_html=True)
        st.markdown(
            '<h1 style="font-size:42px;line-height:1.1;font-weight:800;color:#f8fafc;margin-bottom:18px;">Safer campuses.<br><span style="color:#22d3ee;">Intelligent response.</span></h1>',
            unsafe_allow_html=True
        )
        st.markdown(
            '<p style="color:#94a3b8;font-size:15px;line-height:1.7;max-width:560px;">'
            'CampusGuardian converts incident reports into real-time safety intelligence — empowering student reporters '
            'with quick tracking and providing administration with automated risk triage, evidence review, and emergency dispatch.'
            '</p>',
            unsafe_allow_html=True
        )

        features = [
            ("🤖", "Automated AI Risk Triage", "Identifies hazard severity in seconds and suggests mitigation protocols."),
            ("📍", "GPS & Geospatial Mapping", "Locates incidents across campus blocks with real-time density hotspot detection."),
            ("📷", "Evidence Media Review", "Secure photo uploads with high-definition preview and evidence downloading."),
            ("🆘", "1-Touch Emergency SOS", "Dispatches critical campus alerts to responders with priority geolocation."),
        ]

        for icon, title, desc in features:
            f1, f2 = st.columns([0.1, 0.9])
            with f1:
                st.markdown(f"### {icon}")
            with f2:
                st.markdown(f"**{title}**<br><span style='color:#64748b;font-size:13px;'>{desc}</span>", unsafe_allow_html=True)

    with right:
        st.markdown('<div class="cg-card">', unsafe_allow_html=True)
        st.markdown('<div class="cg-card-header">🔐 Welcome to CampusGuardian</div>', unsafe_allow_html=True)
        login_tab, signup_tab = st.tabs(["Sign In", "Create Account"])

        with login_tab:
            email = st.text_input("Campus Email", placeholder="you@campusguardian.com", key="login_email")
            password = st.text_input("Password", type="password", placeholder="Enter your password", key="login_password")

            if st.button("Sign In Securely →", type="primary", use_container_width=True, key="login_submit"):
                if not email.strip() or not password:
                    st.error("Please enter both email address and password.")
                else:
                    user = login_user(email, password)
                    if user:
                        st.session_state.logged_in = True
                        st.session_state.user = user
                        st.session_state.page = "📊 Overview" if user["role"] == "admin" else "🏠 Dashboard"
                        st.rerun()
                    else:
                        st.error("Invalid email or password. Please verify credentials.")

            st.caption("🛡️ Passwords encrypted with salted PBKDF2 (SHA-256).")
            with st.expander("🔑 Hackathon Demo Credentials"):
                st.info("**Student Account:** `student@campusguardian.com` / `student123`")
                st.info("**Admin Account:** `admin@campusguardian.com` / `admin123`")

        with signup_tab:
            s_name = st.text_input("Full Name *", placeholder="Alex Morgan", key="su_name")
            s_email = st.text_input("Email Address *", placeholder="alex@campus.edu", key="su_email")
            s_dept = st.text_input("Department / Major", placeholder="Computer Science", key="su_dept")
            s_phone = st.text_input("Phone Number", placeholder="+91 98765 43210", key="su_phone")
            s_pass = st.text_input("Password (min 6 chars) *", type="password", key="su_pass")
            s_conf = st.text_input("Confirm Password *", type="password", key="su_conf")

            if st.button("Create Account", use_container_width=True, key="su_submit"):
                if s_pass != s_conf:
                    st.error("Passwords do not match.")
                else:
                    ok, msg = create_account(s_name, s_email, s_pass, s_dept, s_phone)
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)

        st.markdown('</div>', unsafe_allow_html=True)


# ============================================================
# SIDEBAR NAVIGATION
# ============================================================

def show_sidebar(user):
    with st.sidebar:
        st.markdown("### 🛡️ CampusGuardian")
        st.caption(f"{CAMPUS_NAME}")

        unread = get_unread_notification_count(user["id"])
        notif_badge = f" ({unread})" if unread > 0 else ""

        if user["role"] == "admin":
            st.markdown('<span class="cg-badge badge-critical">ADMINISTRATOR</span>', unsafe_allow_html=True)
            pages = [
                "📊 Overview",
                "🚨 Incident Management",
                "👥 User Management",
                "🤖 AI Risk Analysis",
                "🗺️ Incident Map",
                "🔥 Hotspot Detection",
                "📈 Analytics",
                "🔔 Alerts",
                "⚙️ Settings",
            ]
        else:
            st.markdown('<span class="cg-badge badge-open">STUDENT / REPORTER</span>', unsafe_allow_html=True)
            pages = [
                "🏠 Dashboard",
                "🚨 Report Incident",
                "📋 My Reports",
                "📍 Safety Map",
                "🔥 Hotspot Detection",
                "🆘 Emergency SOS",
                f"🔔 Notifications{notif_badge}",
                "👤 Profile",
            ]

        # Use current page index
        curr_page = st.session_state.get("page", pages[0])
        default_idx = pages.index(curr_page) if curr_page in pages else 0

        selected_page = st.radio("Navigation Menu", pages, index=default_idx, label_visibility="collapsed")

        # Strip notification counter from page key for routing
        routed_page = selected_page.split(" (")[0]

        st.divider()
        st.markdown(f"**{user['name']}**")
        st.caption(f"{user['email']}")

        if st.button("🚪 Sign Out", use_container_width=True):
            st.session_state.clear()
            st.rerun()

        return routed_page


# ============================================================
# STUDENT DASHBOARD
# ============================================================

def dashboard(user):
    st.title(f"Welcome back, {user['name']} 👋")
    st.caption("CampusGuardian Student Safety Workspace — Report incidents and monitor resolution status.")

    user_incidents = get_user_incidents(user["id"])
    df = pd.DataFrame(user_incidents)

    total = len(user_incidents)
    active = int((df["status"] != "Resolved").sum()) if not df.empty and "status" in df.columns else 0
    in_progress = int((df["status"] == "In Progress").sum()) if not df.empty and "status" in df.columns else 0
    resolved = int((df["status"] == "Resolved").sum()) if not df.empty and "status" in df.columns else 0

    # Top KPI Metrics
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("📋 My Reports", total)
    m2.metric("🚨 Active Issues", active)
    m3.metric("⏳ In Progress", in_progress)
    m4.metric("✅ Resolved", resolved)

    st.divider()

    # Quick Action Buttons
    st.markdown("### ⚡ Quick Safety Actions")
    q1, q2, q3, q4 = st.columns(4)
    with q1:
        if st.button("🚨 Report Incident", type="primary", use_container_width=True, help="Submit a new campus safety report"):
            st.session_state.page = "🚨 Report Incident"
            st.rerun()
    with q2:
        if st.button("🆘 Emergency SOS", use_container_width=True, help="Trigger rapid response for immediate campus emergencies"):
            st.session_state.page = "🆘 Emergency SOS"
            st.rerun()
    with q3:
        if st.button("📍 Safety Map", use_container_width=True, help="Explore geolocated hazard markers across campus"):
            st.session_state.page = "📍 Safety Map"
            st.rerun()
    with q4:
        if st.button("🔥 Campus Hotspots", use_container_width=True, help="Review hazard density and recurrence analysis"):
            st.session_state.page = "🔥 Hotspot Detection"
            st.rerun()

    st.write("")

    # Submitted Incidents & Status Tracker
    st.markdown("### 📋 Submitted Incidents & Live Status Tracker")
    if not user_incidents:
        st.info("You haven't reported any campus incidents yet. Click **Report Incident** if you notice a hazard.")
    else:
        for inc in user_incidents[:5]:
            status_str = str(inc.get("status", "Open")).title()
            risk_str = str(inc.get("risk") or inc.get("risk_level") or "Low").title()
            priority_str = str(inc.get("priority") or "Normal").title()
            dept_str = inc.get("department") or inc.get("assigned_department") or "Campus Security"

            status_class = f"badge-{status_str.lower().replace(' ', '-')}"
            risk_class = f"badge-{risk_str.lower()}"
            priority_class = {
                "Urgent": "badge-urgent",
                "High": "badge-high",
                "Normal": "badge-normal",
                "Low": "badge-low"
            }.get(priority_str, "badge-normal")

            # Check for photo evidence
            photo_file = resolve_incident_photo(inc.get("photo_path")) if inc.get("photo_path") else None
            photo_badge_html = '<span class="cg-badge" style="background:rgba(56,189,248,0.18); color:#38bdf8; border:1px solid rgba(56,189,248,0.45);">📷 Photo Evidence</span>' if photo_file else ''

            # Calculate progress stage
            stages = ["Open", "Assigned", "In Progress", "Resolved"]
            current_stage_idx = stages.index(status_str) if status_str in stages else 0

            with st.container():
                st.markdown(
                    f'<div class="cg-card" style="padding:18px 20px; margin-bottom:14px;">'
                    f'<div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">'
                    f'<span style="font-weight:750; font-size:16px; color:#f8fafc;">#{inc["id"]} · {inc["title"]}</span>'
                    f'<div style="display:flex; gap:6px; flex-wrap:wrap; align-items:center;">'
                    f'<span class="cg-badge {priority_class}">Priority: {priority_str}</span>'
                    f'<span class="cg-badge {risk_class}">{risk_str} Risk</span>'
                    f'<span class="cg-badge {status_class}">{status_str}</span>'
                    f'{photo_badge_html}'
                    f'</div>'
                    f'</div>'
                    f'<div style="font-size:13px; color:#94a3b8; margin:8px 0 12px 0;">'
                    f'📍 <strong>{inc["location"]}</strong> &nbsp;•&nbsp; 📂 {inc["category"]} &nbsp;•&nbsp; 🏢 {dept_str} &nbsp;•&nbsp; 🕒 {inc["created_at"]}'
                    f'</div>'
                    f'<div class="tracker-container">'
                    f'<div class="tracker-step {"completed" if current_stage_idx >= 0 else "pending"}">'
                    f'<span class="tracker-dot {"dot-completed" if current_stage_idx >= 0 else "dot-pending"}"></span>'
                    f'<span>1. Reported</span>'
                    f'</div>'
                    f'<div class="tracker-line {"active" if current_stage_idx >= 1 else ""}"></div>'
                    f'<div class="tracker-step {"completed" if current_stage_idx >= 1 else "pending"}">'
                    f'<span class="tracker-dot {"dot-completed" if current_stage_idx >= 1 else "dot-pending"}"></span>'
                    f'<span>2. Assigned</span>'
                    f'</div>'
                    f'<div class="tracker-line {"active" if current_stage_idx >= 2 else ""}"></div>'
                    f'<div class="tracker-step {"completed" if current_stage_idx >= 2 else "pending"}">'
                    f'<span class="tracker-dot {"dot-completed" if current_stage_idx >= 2 else "dot-pending"}"></span>'
                    f'<span>3. In Progress</span>'
                    f'</div>'
                    f'<div class="tracker-line {"active" if current_stage_idx >= 3 else ""}"></div>'
                    f'<div class="tracker-step {"completed" if current_stage_idx >= 3 else "pending"}">'
                    f'<span class="tracker-dot {"dot-completed" if current_stage_idx >= 3 else "dot-pending"}"></span>'
                    f'<span>4. Resolved</span>'
                    f'</div>'
                    f'</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )

                if photo_file:
                    with st.expander(f"📷 View Attached Evidence Photo (#{inc['id']})"):
                        st.image(str(photo_file), caption=f"Evidence for Report #{inc['id']}", use_container_width=True)

                if inc.get("admin_note"):
                    st.info(f"📝 **Admin Response Note:** {inc['admin_note']}")


# ============================================================
# REPORT INCIDENT
# ============================================================

def report_incident(user):
    st.title("🚨 Report Incident")
    st.caption("Submit a campus safety issue for instant automated AI risk analysis and response routing.")

    st.info(f"📍 **{CAMPUS_NAME}** &nbsp;•&nbsp; {CAMPUS_ADDRESS}\n\nCampus GPS Reference: **{CAMPUS_LATITUDE:.6f}, {CAMPUS_LONGITUDE:.6f}**")

    categories = [
        "Security", "Security Threat", "Harassment", "Medical Emergency",
        "Fire", "Infrastructure", "Water Leakage", "Pothole",
        "Streetlight", "Traffic", "Lift", "Fighting", "Other",
    ]

    with st.form("incident_report_form"):
        title = st.text_input("Incident Title *", placeholder="e.g. Water leak near ground floor library entrance")

        col_c, col_p = st.columns(2)
        with col_c:
            category = st.selectbox("Hazard Category *", categories)
        with col_p:
            priority = st.selectbox("Priority Level *", ["Urgent", "High", "Normal", "Low"], index=2, help="Indicate the perceived urgency of this hazard")

        location = st.text_input("Specific Campus Location *", value=CAMPUS_ADDRESS, help="Specify building, floor, or landmark")

        description = st.text_area("Detailed Description *", placeholder="Describe the hazard, any injuries, property damage, or immediate risks...", height=120)

        use_campus_gps = st.checkbox("📍 Auto-attach Sapthagiri NPS University Campus GPS", value=True)
        g1, g2 = st.columns(2)
        with g1:
            lat = st.number_input("Latitude", value=float(CAMPUS_LATITUDE), format="%.6f")
        with g2:
            lon = st.number_input("Longitude", value=float(CAMPUS_LONGITUDE), format="%.6f")

        if use_campus_gps:
            lat, lon = CAMPUS_LATITUDE, CAMPUS_LONGITUDE

        photo = st.file_uploader("Attach Incident Photo (JPEG, PNG, WebP)", type=["jpg", "jpeg", "png", "webp"])

        submit = st.form_submit_button("🚨 Submit Incident Report", type="primary", use_container_width=True)

    if not submit:
        return

    if not title.strip() or not location.strip() or not description.strip():
        st.error("Please fill in all required fields (Title, Location, Description).")
        return

    with st.spinner("Processing incident report and analyzing safety risks..."):
        risk = calculate_risk(category, description)
        why = explain_risk(risk)
        dept = assign_department(category)
        photo_path = ""

        if photo:
            try:
                photo_bytes = photo.getvalue()
                test_img = Image.open(io.BytesIO(photo_bytes))
                test_img.verify()
            except Exception as img_err:
                st.error(f"⚠️ Corrupted or unsupported image file: {img_err}. Please upload a valid image (JPEG, PNG).")
                return

            safe_name = re.sub(r'[^a-zA-Z0-9_.-]', '_', Path(photo.name).name)
            filename = f"incident_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}_{safe_name}"
            target_path = PHOTO_FOLDER / filename
            photo_path = f"incident_photos/{filename}"
            try:
                with open(target_path, "wb") as file:
                    file.write(photo_bytes)
            except OSError as error:
                st.error(f"Could not save the incident photo: {error}")
                return

        connection = get_connection()
        try:
            cur = connection.execute("""
                INSERT INTO incidents (
                    user_id, title, category, description, location, latitude, longitude,
                    risk, risk_level, priority, status, department, assigned_department,
                    ai_why, ai_explanation, photo_path, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Open', ?, ?, ?, ?, ?, ?)
            """, (
                user["id"], title.strip(), category, description.strip(), location.strip(),
                lat, lon, risk, risk, priority, dept, dept,
                why, why, photo_path,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))
            inc_id = cur.lastrowid
            connection.commit()
        except sqlite3.Error as err:
            connection.rollback()
            st.error(f"Failed to submit incident: {err}")
            return
        finally:
            connection.close()

        add_notification(user["id"], f"Incident #{inc_id} submitted. Priority: {priority}. AI Risk: {risk}. Routed to: {dept}.")
        try:
            notify_admins(f"New incident #{inc_id} reported: {category} ({priority} Priority) at {location}. Risk: {risk}.")
        except Exception:
            pass

    st.success(f"✅ Incident #{inc_id} submitted successfully!")
    r1, r2, r3, r4 = st.columns(4)
    r1.metric("Assessed Risk", risk)
    r2.metric("Reported Priority", priority)
    r3.metric("Assigned Team", dept)
    r4.metric("Campus GPS", f"{lat:.4f}, {lon:.4f}")

    st.info(f"🤖 **AI Explanation:** {why}")

    if photo_path:
        res = resolve_incident_photo(photo_path)
        if res:
            st.image(str(res), caption=f"Uploaded Evidence Photo · #{inc_id}", width=400)


# ============================================================
# MY REPORTS (STUDENT)
# ============================================================

def my_reports(user):
    st.title("📋 My Reports")
    st.caption("View and track the status of all incidents submitted from your account.")

    incidents = get_user_incidents(user["id"])
    if not incidents:
        st.info("You haven't submitted any incidents yet.")
        if st.button("🚨 Submit Incident Now"):
            st.session_state.page = "🚨 Report Incident"
            st.rerun()
        return

    for inc in incidents:
        risk_str = str(inc.get("risk") or inc.get("risk_level") or "Low").title()
        risk_icon = {"Critical": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🟢"}.get(risk_str, "⚪")
        status_str = str(inc.get("status", "Open")).title()
        priority_str = str(inc.get("priority") or "Normal").title()
        dept_str = inc.get("department") or inc.get("assigned_department") or "Campus Security"

        with st.expander(f"{risk_icon} #{inc['id']} · {inc['title']} · Priority: {priority_str} · [{status_str}]"):
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Risk Level", risk_str)
            m2.metric("Priority", priority_str)
            m3.metric("Current Status", status_str)
            m4.metric("Department", dept_str)

            col1, col2 = st.columns([1.2, 1.0], gap="medium")
            with col1:
                st.write(f"**Category:** {inc['category']}")
                st.write(f"**Location:** {inc['location']}")
                st.write(f"**Reported At:** {inc['created_at']}")
                st.write(f"**Description:**\n{inc['description']}")

                ai_reason = inc.get("ai_why") or inc.get("ai_explanation")
                if ai_reason:
                    st.info(f"🤖 **AI Explanation:** {ai_reason}")
                if inc.get("admin_note"):
                    st.success(f"📝 **Admin Response Note:** {inc['admin_note']}")

            with col2:
                if inc.get("photo_path"):
                    photo_file = resolve_incident_photo(inc["photo_path"])
                    if photo_file:
                        st.image(str(photo_file), caption=f"Evidence Photo #{inc['id']}", use_container_width=True)
                        try:
                            data = photo_file.read_bytes()
                            mime = "image/jpeg" if photo_file.suffix.lower() in [".jpg", ".jpeg"] else "image/png"
                            st.download_button(
                                "⬇️ Download Evidence Photo",
                                data=data,
                                file_name=photo_file.name,
                                mime=mime,
                                key=f"dl_my_rep_{inc['id']}"
                            )
                        except OSError:
                            pass
                    else:
                        st.warning(f"⚠️ Photo registered (`{inc['photo_path']}`) but file not found on disk.")
                else:
                    st.caption("📷 No evidence photograph attached with this report.")


# ============================================================
# SAFETY MAP (STUDENT)
# ============================================================

def safety_map(user):
    st.title("📍 Campus Safety Map")
    st.caption("Live map of active safety hazards and facilities across Sapthagiri NPS University.")

    incidents = get_all_incidents()
    if not incidents:
        st.info("No incident records to display.")
        return

    df = pd.DataFrame(incidents)
    for col in ["latitude", "longitude"]:
        if col not in df.columns:
            df[col] = pd.NA
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["latitude", "longitude"]).copy()
    df = df[
        df["latitude"].between(-90, 90)
        & df["longitude"].between(-180, 180)
        & ~((df["latitude"] == 0) & (df["longitude"] == 0))
    ]

    if df.empty:
        st.info("No incidents have valid GPS coordinates.")
        return

    st.map(df[["latitude", "longitude"]], use_container_width=True)

    cols = [c for c in ["id", "title", "category", "location", "risk", "status", "department", "created_at"] if c in df.columns]
    st.subheader("📌 Mapped Incidents")
    st.dataframe(df[cols].head(15), use_container_width=True, hide_index=True)


# ============================================================
# HOTSPOT DETECTION
# ============================================================

def hotspots():
    st.title("🔥 Campus Hotspot Detection")
    st.caption(f"Smart hazard density and recurrence analysis for {CAMPUS_NAME}.")

    incidents = get_all_incidents()
    if not incidents:
        st.info("No incidents have been reported yet to compute hotspots.")
        return

    df = pd.DataFrame(incidents)
    df["risk"] = df["risk"].fillna("Low").astype(str).str.title()
    df["created_at_dt"] = pd.to_datetime(df["created_at"], errors="coerce")

    risk_points = {"Critical": 4, "High": 3, "Medium": 2, "Low": 1}
    df["risk_points"] = df["risk"].map(risk_points).fillna(1)

    now = pd.Timestamp.now()
    days_old = (now - df["created_at_dt"]).dt.total_seconds() / 86400
    days_old = days_old.fillna(9999).clip(lower=0)

    df["recent_points"] = 0.0
    df.loc[days_old <= 7, "recent_points"] = 2.0
    df.loc[(days_old > 7) & (days_old <= 30), "recent_points"] = 1.0

    hotspot = (
        df.groupby("location", as_index=False)
        .agg(
            Incidents=("location", "size"),
            Risk_Points=("risk_points", "sum"),
            Recent_Points=("recent_points", "sum"),
            High_Risk=("risk", lambda s: int(s.isin(["Critical", "High"]).sum())),
            Categories=("category", "nunique"),
        )
    )

    hotspot["Hotspot Score"] = (hotspot["Incidents"] + hotspot["Risk_Points"] + hotspot["Recent_Points"]).round(1)
    hotspot = hotspot.sort_values("Hotspot Score", ascending=False).reset_index(drop=True)

    # Top summary metrics
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Total Incidents", len(df))
    s2.metric("Unique Locations", df["location"].nunique())
    s3.metric("High/Critical Incidents", int(df["risk"].isin(["Critical", "High"]).sum()))
    s4.metric("Top Hotspot Score", float(hotspot.iloc[0]["Hotspot Score"]) if not hotspot.empty else 0)

    st.divider()

    # Bar chart of top hotspots
    st.subheader("📊 Top Hotspot Rankings")
    top_chart = hotspot.head(10).sort_values("Hotspot Score", ascending=True)
    fig = px.bar(
        top_chart,
        x="Hotspot Score",
        y="location",
        orientation="h",
        text="Hotspot Score",
        title="Incident Concentration Score by Campus Location",
        labels={"Hotspot Score": "AI Hotspot Score", "location": "Location"}
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(height=400, margin=dict(l=20, r=40, t=50, b=40))
    st.plotly_chart(fig, use_container_width=True)

    # Display Heatmap
    st.subheader("🗺️ Geospatial Risk Density")
    render_campus_heatmap(df)


# ============================================================
# EMERGENCY SOS
# ============================================================

def emergency(user=None):
    st.title("🆘 Emergency Response Center")
    st.caption("Immediate safety protocols, emergency dispatch, and direct campus security contact.")

    # Urgent Helplines Banner
    st.error("""
    ### 🚨 Immediate Life-Safety Numbers (India)
    • **112** — All-in-One National Emergency Helpline  
    • **101** — Fire & Rescue Services  
    • **102** — Medical Ambulance  
    • **Campus Security Control Room:** +91 80 2839 8888 (Internal Ext: 911)
    """)

    st.markdown("---")
    st.markdown("### 🚨 Direct Emergency SOS Dispatch")
    st.write("Trigger this if you or another individual are facing an active life-safety emergency on campus.")

    emergency_type = st.selectbox("Type of Emergency", [
        "Medical Emergency", "Fire", "Violence / Fighting",
        "Elevator / Lift Trapped", "Security Threat", "Infrastructure Hazard"
    ])
    sos_location = st.text_input("Emergency Location", value=CAMPUS_ADDRESS)
    sos_details = st.text_area("Situation Details", placeholder="Briefly describe what is happening and any trapped/injured individuals...")
    confirm = st.checkbox("I confirm this is an authentic life-safety emergency.")

    if st.button("🚨 DISPATCH EMERGENCY SOS NOW", type="primary", use_container_width=True):
        if not confirm:
            st.warning("Please confirm that this is an authentic emergency.")
            return

        desc = sos_details.strip() or f"Emergency SOS triggered: {emergency_type}"
        user_id = user["id"] if user else 1
        user_name = user["name"] if user else "Campus Reporter"

        conn = get_connection()
        try:
            cur = conn.execute("""
                INSERT INTO incidents (
                    user_id, title, category, description, location, latitude, longitude,
                    risk, status, department, ai_why, emergency, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'Critical', 'Open', 'Campus Security', 'Emergency SOS automatically triaged as Critical for immediate physical dispatch.', 1, ?)
            """, (
                user_id, f"🚨 EMERGENCY SOS: {emergency_type}", emergency_type, desc,
                sos_location, CAMPUS_LATITUDE, CAMPUS_LONGITUDE,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))
            inc_id = cur.lastrowid
            conn.commit()
        finally:
            conn.close()

        add_notification(user_id, f"🚨 Emergency SOS #{inc_id} dispatched. Security team alerted.")
        notify_admins(f"🚨 CRITICAL SOS #{inc_id}: {emergency_type} at {sos_location} by {user_name}!")

        st.success(f"Emergency SOS #{inc_id} Dispatched! Campus Security and First Responders have been notified.")
        st.balloons()


# ============================================================
# NOTIFICATIONS (IN-APP)
# ============================================================

def notifications(user):
    st.title("🔔 Notifications")
    st.caption("Live updates regarding your submitted incidents and security announcements.")

    if st.button("Mark All as Read"):
        mark_notifications_read(user["id"])
        st.success("All notifications marked as read.")
        st.rerun()

    notifs = get_notifications(user["id"])
    if not notifs:
        st.info("You have no notifications at this time.")
        return

    for n in notifs:
        icon = "⚪" if n.get("is_read") else "🔵"
        st.markdown(
            f'<div class="cg-card" style="padding:12px 16px; margin-bottom:8px;">'
            f'<div style="font-size:14px; color:#f8fafc;">{icon} {n["message"]}</div>'
            f'<div style="font-size:11px; color:#64748b; margin-top:4px;">🕒 {n["created_at"]}</div>'
            f'</div>',
            unsafe_allow_html=True
        )


# ============================================================
# PROFILE
# ============================================================

def profile(user):
    st.title("👤 User Profile")
    st.caption("Account identity and safety workspace details.")

    col1, col2 = st.columns([1, 1.2])
    with col1:
        st.markdown('<div class="cg-card">', unsafe_allow_html=True)
        st.markdown("### Profile Information")
        st.write(f"**Name:** {user['name']}")
        st.write(f"**Email:** {user['email']}")
        st.write(f"**Role:** {user['role'].upper()}")
        st.write(f"**Department:** {user.get('department') or 'Student Body'}")
        st.write(f"**Phone:** {user.get('phone') or 'Not provided'}")
        st.write(f"**Member Since:** {user.get('created_at', '2026')}")
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        user_inc = get_user_incidents(user["id"])
        st.markdown('<div class="cg-card">', unsafe_allow_html=True)
        st.markdown("### Reporting History")
        st.metric("Total Submitted Reports", len(user_inc))
        resolved = sum(1 for i in user_inc if i.get("status") == "Resolved")
        st.metric("Resolved Issues", resolved)
        st.markdown('</div>', unsafe_allow_html=True)


# ============================================================
# ROLE-BASED ACCESS CONTROL (RBAC) & ADMIN PAGES
# ============================================================

def check_admin_access():
    """Verify that current session belongs to an authenticated administrator."""
    user = st.session_state.get("user")
    if not st.session_state.get("logged_in") or not user or str(user.get("role", "")).lower() != "admin":
        st.error("⛔ Access Denied: Administrator privileges required to access this portal.")
        st.info("Please sign in with an authorized campus administrator account.")
        return False
    return True


# ============================================================
# ADMIN: OVERVIEW & COMMAND CENTER
# ============================================================

def admin_overview():
    if not check_admin_access():
        return
    st.title("🛡️ Campus Safety Command Center")
    st.caption(f"Real-time safety operations, risk density, and triage for {CAMPUS_NAME}.")

    incidents = get_all_incidents()
    df = pd.DataFrame(incidents)

    if df.empty:
        st.info("No incidents have been reported yet.")
        return

    for col in ["risk", "status", "category", "department"]:
        if col in df.columns:
            df[col] = df[col].astype(str)

    df["created_dt"] = pd.to_datetime(df["created_at"], errors="coerce")

    total = len(df)
    critical = int((df["risk"] == "Critical").sum())
    high = int(df["risk"].isin(["High", "Critical"]).sum())
    active = int((df["status"] != "Resolved").sum())
    resolved = int((df["status"] == "Resolved").sum())
    recent_7d = int((df["created_dt"] >= pd.Timestamp.now() - pd.Timedelta(days=7)).sum())
    resolution_rate = round((resolved / max(total, 1)) * 100, 1)

    safety_score = calculate_campus_safety_score(df)
    score_lbl, score_desc = safety_score_label(safety_score)

    # Command Center KPI Row
    k1, k2, k3, k4, k5, k6 = st.columns(6)
    k1.metric("Total Reports", total)
    k2.metric("Critical / High", high)
    k3.metric("Active Open", active)
    k4.metric("Resolved", resolved)
    k5.metric("7-Day Velocity", recent_7d)
    k6.metric("Resolution %", f"{resolution_rate}%")

    st.write("")
    st.markdown("#### 🛡️ Campus Operational Safety Score")
    st.progress(safety_score / 100, text=f"{safety_score}/100 · {score_lbl} — {score_desc}")

    st.divider()

    # AI Safety Insight
    st.subheader("🤖 Automated Safety Intelligence")
    st.info(generate_safety_insight(df))

    # Analytical Charts Row
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🚨 Risk Level Distribution")
        risk_counts = df["risk"].value_counts().reindex(["Critical", "High", "Medium", "Low"], fill_value=0).reset_index()
        risk_counts.columns = ["Risk", "Count"]
        rf = px.bar(
            risk_counts, x="Risk", y="Count", color="Risk",
            color_discrete_map={"Critical": "#ef4444", "High": "#f97316", "Medium": "#eab308", "Low": "#22c55e"},
            text="Count"
        )
        rf.update_traces(textposition="outside", textfont=dict(color="#f8fafc", size=13))
        rf.update_layout(
            height=340,
            showlegend=False,
            margin=dict(l=15, r=15, t=30, b=25),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#94a3b8", family="Plus Jakarta Sans, sans-serif"),
            xaxis=dict(gridcolor="rgba(255,255,255,0.06)", showline=False, color="#cbd5e1"),
            yaxis=dict(gridcolor="rgba(255,255,255,0.06)", showline=False, color="#cbd5e1")
        )
        st.plotly_chart(rf, use_container_width=True)

    with c2:
        st.subheader("📌 Resolution Status Breakdown")
        status_counts = df["status"].value_counts().reset_index()
        status_counts.columns = ["Status", "Count"]
        sf = px.pie(
            status_counts, names="Status", values="Count", hole=0.5,
            color="Status",
            color_discrete_map={
                "Open": "#3b82f6",
                "Assigned": "#a855f7",
                "In Progress": "#f59e0b",
                "Resolved": "#10b981"
            }
        )
        sf.update_traces(textposition="inside", textinfo="percent+label", textfont=dict(color="#ffffff", size=12))
        sf.update_layout(
            height=340,
            showlegend=False,
            margin=dict(l=15, r=15, t=30, b=25),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#cbd5e1", family="Plus Jakarta Sans, sans-serif")
        )
        st.plotly_chart(sf, use_container_width=True)

    # Geospatial Heatmap
    st.subheader("🗺️ Campus Risk Heatmap")
    render_campus_heatmap(df, "Campus Risk Distribution")

    # Active Incidents Table
    st.subheader("🚨 Active Incidents Requiring Administrative Follow-Up")
    active_df = df[df["status"] != "Resolved"].copy()
    if active_df.empty:
        st.success("🟢 No active unresolved incidents currently on record.")
    else:
        disp_cols = [c for c in ["id", "title", "category", "location", "risk", "status", "department", "reporter", "created_at"] if c in active_df.columns]
        st.dataframe(active_df[disp_cols].head(10), use_container_width=True, hide_index=True)


# ============================================================
# ADMIN: INCIDENT MANAGEMENT
# ============================================================

def incident_management():
    if not check_admin_access():
        return
    st.title("🚨 Incident Management")
    st.caption("Administrator triage & response center — review evidence, assign teams, and manage resolution workflow.")

    incidents = get_all_incidents()
    if not incidents:
        st.info("No incidents have been reported yet.")
        return

    df = pd.DataFrame(incidents)

    # Filter controls - Row 1 (Category, Risk, Status, Priority)
    f1, f2, f3, f4 = st.columns(4)
    with f1:
        risk_filter = st.selectbox("Risk Filter", ["All", "Critical", "High", "Medium", "Low"], key="admin_risk_flt")
    with f2:
        status_filter = st.selectbox("Status Filter", ["All", "Open", "Assigned", "In Progress", "Resolved"], key="admin_status_flt")
    with f3:
        priority_filter = st.selectbox("Priority Filter", ["All", "Urgent", "High", "Normal", "Low"], key="admin_pri_flt")
    with f4:
        cats = sorted(list(set(str(x) for x in df["category"].dropna().unique()))) if "category" in df.columns else []
        category_filter = st.selectbox("Category Filter", ["All"] + cats, key="admin_cat_flt")

    # Filter controls - Row 2 (Sort Order & Search Query)
    s1, s2 = st.columns([1.2, 2.0])
    with s1:
        sort_order = st.selectbox(
            "Triage Queue & Sort Order",
            [
                "🚨 Priority Queue (Urgent & Critical First)",
                "🕒 Newest First (Default)",
                "⏳ Active Unresolved First",
                "✅ Resolved First",
                "🔢 Incident ID (Ascending)"
            ],
            key="admin_sort_order"
        )
    with s2:
        search_query = st.text_input("Search Reports", placeholder="Filter by title, location, reporter, description...", key="admin_srch_query")

    filtered = list(incidents)
    if risk_filter != "All":
        filtered = [x for x in filtered if str(x.get("risk") or x.get("risk_level") or "").title() == risk_filter]
    if status_filter != "All":
        filtered = [x for x in filtered if str(x.get("status") or "").title() == status_filter]
    if category_filter != "All":
        filtered = [x for x in filtered if str(x.get("category") or "") == category_filter]
    if priority_filter != "All":
        filtered = [x for x in filtered if str(x.get("priority") or "Normal").title() == priority_filter]
    if search_query.strip():
        q = search_query.strip().lower()
        filtered = [
            x for x in filtered
            if q in f"{x.get('title','')} {x.get('location','')} {x.get('reporter','')} {x.get('description','')} {x.get('category','')}".lower()
        ]

    # Apply Triage Sorting
    risk_rank = {"Critical": 4, "High": 3, "Medium": 2, "Low": 1}
    priority_rank = {"Urgent": 4, "High": 3, "Normal": 2, "Low": 1}

    if sort_order == "🚨 Priority Queue (Urgent & Critical First)":
        filtered.sort(
            key=lambda x: (
                1 if str(x.get("status", "Open")).title() != "Resolved" else 0,
                risk_rank.get(str(x.get("risk") or x.get("risk_level") or "Low").title(), 1),
                priority_rank.get(str(x.get("priority") or "Normal").title(), 2),
                x.get("id", 0)
            ),
            reverse=True
        )
    elif sort_order == "⏳ Active Unresolved First":
        filtered.sort(
            key=lambda x: (
                1 if str(x.get("status", "Open")).title() != "Resolved" else 0,
                x.get("id", 0)
            ),
            reverse=True
        )
    elif sort_order == "✅ Resolved First":
        filtered.sort(
            key=lambda x: (
                1 if str(x.get("status", "Open")).title() == "Resolved" else 0,
                x.get("id", 0)
            ),
            reverse=True
        )
    elif sort_order == "🔢 Incident ID (Ascending)":
        filtered.sort(key=lambda x: x.get("id", 0))
    else:  # "🕒 Newest First (Default)"
        filtered.sort(key=lambda x: x.get("id", 0), reverse=True)

    st.caption(f"Showing **{len(filtered)}** of **{len(incidents)}** incident report(s)")
    if not filtered:
        st.warning("No incidents match the active filters.")
        return

    department_options = [
        "Campus Security",
        "Maintenance",
        "Electrical Maintenance",
        "Lift & Elevator Maintenance",
        "Medical Unit",
        "Fire & Safety",
        "Student Welfare",
        "Campus Administration",
    ]
    status_options = ["Open", "Assigned", "In Progress", "Resolved"]

    for incident in filtered:
        risk_str = str(incident.get("risk") or incident.get("risk_level") or "Low").title()
        risk_badge = {"Critical": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🟢"}.get(risk_str, "⚪")
        status_str = str(incident.get("status", "Open")).title()
        if status_str not in status_options:
            status_str = "Open"
        priority_str = str(incident.get("priority") or "Normal").title()
        dept_str = incident.get("department") or incident.get("assigned_department") or "Campus Security"

        status_class = f"badge-{status_str.lower().replace(' ', '-')}"
        risk_class = f"badge-{risk_str.lower()}"
        priority_class = {
            "Urgent": "badge-urgent",
            "High": "badge-high",
            "Normal": "badge-normal",
            "Low": "badge-low"
        }.get(priority_str, "badge-normal")

        with st.expander(f"{risk_badge} #{incident['id']} · {incident.get('title', 'Incident')} · {risk_str} Risk · Priority: {priority_str} · [{status_str}]"):
            # If critical/high risk and unresolved, show prominent urgency banner
            if risk_str in ["Critical", "High"] and status_str != "Resolved":
                st.markdown(
                    f'<div style="background:rgba(239, 68, 68, 0.15); border:1px solid rgba(239, 68, 68, 0.45); border-radius:8px; padding:8px 14px; margin-bottom:12px; font-size:13px; color:#fca5a5; display:flex; align-items:center; gap:8px;">'
                    f'<span>🚨</span> <strong>High Priority Attention Required:</strong> Active {risk_str}-risk hazard awaiting completion.'
                    f'</div>',
                    unsafe_allow_html=True
                )

            # Metric summary row
            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("Risk Level", risk_str)
            m2.metric("Priority", priority_str)
            m3.metric("Status", status_str)
            m4.metric("Department", dept_str)
            m5.metric("Reporter", incident.get("reporter") or "Student / Unknown")

            col_left, col_right = st.columns([1.2, 1.0], gap="medium")

            with col_left:
                st.markdown("#### 📋 Incident Details")
                st.write(f"**Category:** {incident.get('category')}")
                st.write(f"**Location:** {incident.get('location')}")
                st.write(f"**Reported At:** {incident.get('created_at')}")
                st.write(f"**Description:**\n{incident.get('description')}")

                ai_reason = incident.get("ai_why") or incident.get("ai_explanation")
                if ai_reason:
                    st.info(f"🤖 **AI Risk Assessment:**\n{ai_reason}")

                if incident.get("admin_note"):
                    st.warning(f"📝 **Current Admin Note:**\n{incident['admin_note']}")

            with col_right:
                st.markdown("#### 📷 Evidence Photograph")
                photo_path = incident.get("photo_path")
                if photo_path:
                    photo_file = resolve_incident_photo(photo_path)
                    if photo_file:
                        st.image(str(photo_file), caption=f"Evidence Photo · #{incident['id']}", use_container_width=True)
                        try:
                            data = photo_file.read_bytes()
                            mime = "image/jpeg" if photo_file.suffix.lower() in [".jpg", ".jpeg"] else "image/png"
                            st.download_button(
                                "⬇️ Download Evidence Photo",
                                data=data,
                                file_name=photo_file.name,
                                mime=mime,
                                key=f"dl_admin_{incident['id']}"
                            )
                        except OSError:
                            pass
                    else:
                        st.warning(f"⚠️ Photo registered (`{photo_path}`) but file is currently inaccessible on disk.")
                else:
                    st.caption("📷 No evidence photograph attached for this incident.")

            st.divider()
            st.markdown("#### 🛠️ Response Actions & Triage")
            c1, c2 = st.columns(2)

            all_depts = list(department_options)
            if dept_str not in all_depts:
                all_depts.append(dept_str)

            with c1:
                new_status = st.selectbox(
                    "Update Status",
                    status_options,
                    index=status_options.index(status_str),
                    key=f"status_select_{incident['id']}"
                )
            with c2:
                new_dept = st.selectbox(
                    "Assign Department",
                    all_depts,
                    index=all_depts.index(dept_str),
                    key=f"dept_select_{incident['id']}"
                )

            new_note = st.text_area(
                "Administrator Response Note",
                value=incident.get("admin_note") or "",
                placeholder="Document resolution progress or instructions for response teams...",
                key=f"admin_note_input_{incident['id']}",
                height=90
            )

            if st.button("💾 Save Incident Update", type="primary", key=f"save_btn_{incident['id']}", use_container_width=True):
                connection = get_connection()
                try:
                    connection.execute(
                        """
                        UPDATE incidents
                        SET status = ?, department = ?, assigned_department = ?, admin_note = ?
                        WHERE id = ?
                        """,
                        (new_status, new_dept, new_dept, new_note.strip(), incident["id"])
                    )
                    connection.commit()
                finally:
                    connection.close()

                # Notify reporter if user_id is known
                if incident.get("user_id"):
                    add_notification(
                        incident["user_id"],
                        f"Incident #{incident['id']} status updated to '{new_status}' ({new_dept})."
                    )
                    if new_status == "Resolved":
                        add_notification(
                            incident["user_id"],
                            f"✅ Incident #{incident['id']} has been successfully marked as Resolved."
                        )

                st.success(f"Incident #{incident['id']} updated successfully!")
                st.rerun()


# ============================================================
# ADMIN: USER MANAGEMENT
# ============================================================

def user_management():
    if not check_admin_access():
        return
    st.title("👥 User & Role Management")
    st.caption("Review registered students, safety staff, and administrator credentials.")

    conn = get_connection()
    users = conn.execute("SELECT id, name, email, role, department, phone, created_at FROM users ORDER BY id DESC").fetchall()
    conn.close()

    df = pd.DataFrame([dict(u) for u in users])

    u1, u2, u3 = st.columns(3)
    u1.metric("Registered Accounts", len(df))
    admin_cnt = sum(1 for u in users if u["role"] == "admin")
    u2.metric("Administrators", admin_cnt)
    u3.metric("Student Reporters", len(df) - admin_cnt)

    st.subheader("All User Accounts")
    st.dataframe(df, use_container_width=True, hide_index=True)


# ============================================================
# ADMIN: AI RISK ANALYSIS
# ============================================================

def ai_analysis():
    if not check_admin_access():
        return
    st.title("🤖 Explainable AI Risk Analysis")
    st.caption("Detailed heuristic assessments and reasoning breakdown for each reported campus event.")

    incidents = get_all_incidents()
    if not incidents:
        st.info("No incidents on record.")
        return

    for inc in incidents:
        risk_str = str(inc.get("risk", "Low")).title()
        badge = {"Critical": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🟢"}.get(risk_str, "⚪")

        with st.expander(f"{badge} #{inc['id']} · {inc['title']} · [{risk_str}]"):
            st.markdown(f"**Hazard Category:** {inc['category']} &nbsp;|&nbsp; **Location:** {inc['location']}")
            st.write(f"**Reporter's Narrative:**\n{inc['description']}")
            st.info(f"**🤖 AI Reason & Assessment:**\n{inc.get('ai_why') or explain_risk(risk_str)}")
            st.write(f"**Assigned Response Team:** {inc.get('department')}")


# ============================================================
# ADMIN: INCIDENT MAP
# ============================================================

def admin_map():
    if not check_admin_access():
        return
    st.title("🗺️ Incident Map & Geospatial Tracking")
    st.caption(f"Spatial distribution of reported events across {CAMPUS_NAME}.")

    incidents = get_all_incidents()
    if not incidents:
        st.info("No incidents available.")
        return

    df = pd.DataFrame(incidents)
    for col in ["latitude", "longitude"]:
        if col not in df.columns:
            df[col] = pd.NA
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["latitude", "longitude"]).copy()
    df = df[
        df["latitude"].between(-90, 90)
        & df["longitude"].between(-180, 180)
        & ~((df["latitude"] == 0) & (df["longitude"] == 0))
    ]

    if df.empty:
        st.info("No incidents have valid GPS coordinates.")
        return

    st.map(df[["latitude", "longitude"]], use_container_width=True)
    st.subheader("All Geolocated Records")
    cols = [c for c in ["id", "title", "category", "location", "risk", "status", "department", "reporter", "created_at"] if c in df.columns]
    st.dataframe(df[cols], use_container_width=True, hide_index=True)


# ============================================================
# ADMIN: ANALYTICS
# ============================================================

def analytics():
    if not check_admin_access():
        return
    st.title("📈 Safety Analytics & Trends")
    st.caption("Quantitative insights into incident distribution, department workloads, and resolution rates.")

    incidents = get_all_incidents()
    if not incidents:
        st.info("No incidents to analyze.")
        return

    df = pd.DataFrame(incidents)

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("📂 Incidents by Department")
        dept_counts = df["department"].fillna("Unassigned").value_counts().reset_index()
        dept_counts.columns = ["Department", "Incidents"]
        df_fig = px.bar(
            dept_counts, x="Incidents", y="Department", orientation="h", text="Incidents",
            color="Incidents",
            color_continuous_scale="Tealgrn"
        )
        df_fig.update_traces(textposition="outside", textfont=dict(color="#f8fafc", size=12))
        df_fig.update_layout(
            height=360,
            showlegend=False,
            margin=dict(l=15, r=15, t=30, b=25),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#94a3b8", family="Plus Jakarta Sans, sans-serif"),
            xaxis=dict(gridcolor="rgba(255,255,255,0.06)", showline=False, color="#cbd5e1"),
            yaxis=dict(gridcolor="rgba(255,255,255,0.06)", showline=False, color="#cbd5e1")
        )
        st.plotly_chart(df_fig, use_container_width=True)

    with c2:
        st.subheader("🏷️ Incidents by Category")
        cat_counts = df["category"].fillna("Other").value_counts().reset_index()
        cat_counts.columns = ["Category", "Incidents"]
        cf_fig = px.pie(
            cat_counts, names="Category", values="Incidents", hole=0.45,
            color_discrete_sequence=px.colors.qualitative.Prism
        )
        cf_fig.update_traces(textposition="inside", textinfo="percent+label", textfont=dict(color="#ffffff", size=11))
        cf_fig.update_layout(
            height=360,
            showlegend=False,
            margin=dict(l=15, r=15, t=30, b=25),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#cbd5e1", family="Plus Jakarta Sans, sans-serif")
        )
        st.plotly_chart(cf_fig, use_container_width=True)


# ============================================================
# ADMIN: ALERTS
# ============================================================

def alerts():
    if not check_admin_access():
        return
    st.title("🔔 Security Alerts & Critical Hazards")
    st.caption("High-priority safety issues requiring immediate resolution.")

    incidents = get_all_incidents()
    high_incidents = [i for i in incidents if str(i.get("risk")).title() in ["Critical", "High"] and i.get("status") != "Resolved"]

    if not high_incidents:
        st.success("🟢 No active Critical or High risk alerts at this time.")
        return

    for inc in high_incidents:
        risk_str = str(inc.get("risk")).title()
        badge = "🚨" if risk_str == "Critical" else "⚠️"
        st.error(f"{badge} **#{inc['id']} — {inc['title']}**\n\nLocation: {inc['location']} | Status: {inc['status']} | Department: {inc['department']}\n\n{inc['description']}")


# ============================================================
# ADMIN: SETTINGS
# ============================================================

def settings():
    if not check_admin_access():
        return
    st.title("⚙️ System Configuration")
    st.caption("CampusGuardian technical configuration and database health.")

    st.info(f"**Campus Reference:** {CAMPUS_NAME}\n\n**Address:** {CAMPUS_ADDRESS}\n\n**GPS Reference:** {CAMPUS_LATITUDE:.6f}, {CAMPUS_LONGITUDE:.6f}")

    st.write("### System Architecture")
    st.write("• **Database:** SQLite (`campusguardian.db`)")
    st.write("• **Evidence Storage:** Local file system (`incident_photos/`)")
    st.write("• **Authentication:** Salted PBKDF2 with SHA-256 fallback auto-upgrade")
    st.write("• **AI Engine:** Heuristic risk inference & explainability engine")

    if st.button("🔄 Optimize & Vacuum Database", use_container_width=True):
        conn = get_connection()
        conn.execute("VACUUM")
        conn.close()
        st.success("Database vacuumed and optimized successfully.")


# ============================================================
# ROUTING & APPLICATION ENTRY POINT
# ============================================================

def main():
    initialize_database()

    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "user" not in st.session_state:
        st.session_state.user = None
    if "page" not in st.session_state:
        st.session_state.page = "🏠 Dashboard"

    if not st.session_state.logged_in or not st.session_state.user:
        login_page()
        return

    user = st.session_state.user
    inject_custom_css()
    page = show_sidebar(user)
    st.session_state.page = page

    # Role separation and route protection
    admin_pages = {
        "📊 Overview", "🚨 Incident Management", "👥 User Management",
        "🤖 AI Risk Analysis", "🗺️ Incident Map", "📈 Analytics",
        "🔔 Alerts", "⚙️ Settings"
    }

    if user.get("role") == "admin":
        admin_routes = {
            "📊 Overview": admin_overview,
            "🚨 Incident Management": incident_management,
            "👥 User Management": user_management,
            "🤖 AI Risk Analysis": ai_analysis,
            "🗺️ Incident Map": admin_map,
            "🔥 Hotspot Detection": hotspots,
            "📈 Analytics": analytics,
            "🔔 Alerts": alerts,
            "⚙️ Settings": settings,
        }
        handler = admin_routes.get(page, admin_overview)
        handler()
    else:
        # Prevent any student user from navigating to admin pages
        if page in admin_pages:
            st.warning("⚠️ Restricted Area: Redirected to Student Dashboard.")
            st.session_state.page = "🏠 Dashboard"
            page = "🏠 Dashboard"

        user_routes = {
            "🏠 Dashboard": lambda: dashboard(user),
            "🚨 Report Incident": lambda: report_incident(user),
            "📋 My Reports": lambda: my_reports(user),
            "📍 Safety Map": lambda: safety_map(user),
            "🔥 Hotspot Detection": hotspots,
            "🆘 Emergency SOS": lambda: emergency(user),
            "🔔 Notifications": lambda: notifications(user),
            "👤 Profile": lambda: profile(user),
        }
        handler = user_routes.get(page, lambda: dashboard(user))
        handler()


if __name__ == "__main__":
    main()
