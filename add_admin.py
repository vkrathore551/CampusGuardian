import streamlit as st

import sqlite3

import hashlib

from datetime import datetime

from pathlib import Path
from textwrap import dedent

import pandas as pd

import plotly.express as px
import plotly.graph_objects as go





# ============================================================

# CONFIG

# ============================================================



st.set_page_config(

    page_title="CampusGuardian AI",

    page_icon="🛡️",

    layout="wide"

)



BASE_DIR = Path(__file__).resolve().parent
DB_NAME = str(BASE_DIR / "campusguardian.db")
PHOTO_FOLDER = BASE_DIR / "incident_photos"
PHOTO_FOLDER.mkdir(parents=True, exist_ok=True)

# Sapthagiri NPS University campus reference location.
CAMPUS_NAME = "Sapthagiri NPS University"
CAMPUS_ADDRESS = "#14/5, Chikkasandra, Hesarghatta Main Road, Bengaluru, Karnataka 560057"
CAMPUS_LATITUDE = 13.069473
CAMPUS_LONGITUDE = 77.502191





# ============================================================

# DATABASE

# ============================================================



def get_connection():

    connection = sqlite3.connect(DB_NAME)

    connection.row_factory = sqlite3.Row

    return connection





def hash_password(password):

    return hashlib.sha256(

        password.encode("utf-8")

    ).hexdigest()





def resolve_incident_photo(photo_value):
    """Resolve an incident photo reliably even if the app was started from another folder."""
    if not photo_value:
        return None

    raw = Path(str(photo_value))
    candidates = []

    if raw.is_absolute():
        candidates.append(raw)
    else:
        candidates.append(BASE_DIR / raw)
        candidates.append(Path.cwd() / raw)

    # Also support older records that stored a path from a previous project location.
    candidates.append(PHOTO_FOLDER / raw.name)
    candidates.append(BASE_DIR / "incident_photos" / raw.name)

    seen = set()
    for candidate in candidates:
        try:
            candidate = candidate.resolve()
        except OSError:
            continue
        key = str(candidate).lower()
        if key in seen:
            continue
        seen.add(key)
        if candidate.exists() and candidate.is_file():
            return candidate

    return None


def initialize_database():
    """Create tables and migrate older CampusGuardian SQLite databases safely."""
    connection = get_connection()

    try:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user',
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
                status TEXT DEFAULT 'Open',
                department TEXT DEFAULT 'Campus Security',
                ai_why TEXT DEFAULT '',
                photo_path TEXT DEFAULT '',
                admin_note TEXT DEFAULT '',
                created_at TEXT NOT NULL
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                message TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        def columns(table_name):
            return {
                row["name"]
                for row in connection.execute(
                    f"PRAGMA table_info({table_name})"
                ).fetchall()
            }

        def add_column(table_name, column_name, definition):
            if column_name not in columns(table_name):
                connection.execute(
                    f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}"
                )

        # Migrate old users table.
        for name, definition in [
            ("name", "TEXT"),
            ("email", "TEXT"),
            ("password", "TEXT"),
            ("role", "TEXT DEFAULT 'user'"),
            ("created_at", "TEXT"),
        ]:
            add_column("users", name, definition)

        # Migrate old incidents table.
        for name, definition in [
            ("user_id", "INTEGER"),
            ("title", "TEXT"),
            ("category", "TEXT"),
            ("description", "TEXT"),
            ("location", "TEXT"),
            ("latitude", "REAL DEFAULT 0"),
            ("longitude", "REAL DEFAULT 0"),
            ("risk", "TEXT DEFAULT 'Low'"),
            ("status", "TEXT DEFAULT 'Open'"),
            ("department", "TEXT DEFAULT 'Campus Security'"),
            ("ai_why", "TEXT DEFAULT ''"),
            ("photo_path", "TEXT DEFAULT ''"),
            ("admin_note", "TEXT DEFAULT ''"),
            ("is_demo", "INTEGER DEFAULT 0"),
            ("created_at", "TEXT"),
        ]:
            add_column("incidents", name, definition)

        # Migrate old notifications table.
        for name, definition in [
            ("user_id", "INTEGER"),
            ("message", "TEXT"),
            ("created_at", "TEXT"),
        ]:
            add_column("notifications", name, definition)

        # Fill missing legacy campus location data so old incidents remain mappable.
        connection.execute(
            "UPDATE incidents SET location = ? WHERE location IS NULL OR TRIM(location) = ''",
            (CAMPUS_ADDRESS,),
        )
        connection.execute(
            """
            UPDATE incidents
            SET latitude = ?, longitude = ?
            WHERE latitude IS NULL OR longitude IS NULL
               OR (latitude = 0 AND longitude = 0)
            """,
            (CAMPUS_LATITUDE, CAMPUS_LONGITUDE),
        )

        # Repair NULL values created by older schemas.
        connection.execute("""
            UPDATE incidents
            SET department = 'Campus Security'
            WHERE department IS NULL OR TRIM(department) = ''
        """)
        connection.execute("""
            UPDATE incidents
            SET risk = 'Low'
            WHERE risk IS NULL OR TRIM(risk) = ''
        """)
        connection.execute("""
            UPDATE incidents
            SET status = 'Open'
            WHERE status IS NULL OR TRIM(status) = ''
        """)
        connection.execute("""
            UPDATE incidents
            SET ai_why = ''
            WHERE ai_why IS NULL
        """)
        connection.execute("""
            UPDATE incidents
            SET photo_path = ''
            WHERE photo_path IS NULL
        """)
        connection.execute("""
            UPDATE incidents
            SET is_demo = 0
            WHERE is_demo IS NULL
        """)

        connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_incidents_user_id
            ON incidents(user_id)
        """)
        connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_incidents_status
            ON incidents(status)
        """)
        connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_incidents_risk
            ON incidents(risk)
        """)
        connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_incidents_category
            ON incidents(category)
        """)
        connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_notifications_user_id
            ON notifications(user_id)
        """)

        # Demo accounts. Ensure they exist even if the database already contains users.
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        student_exists = connection.execute(
            "SELECT 1 FROM users WHERE email=?",
            ("student@campusguardian.com",),
        ).fetchone()
        if not student_exists:
            connection.execute(
                "INSERT INTO users (name, email, password, role, created_at) VALUES (?, ?, ?, ?, ?)",
                ("Demo Student", "student@campusguardian.com", hash_password("student123"), "user", now),
            )

        admin_exists = connection.execute(
            "SELECT 1 FROM users WHERE email=?",
            ("admin@campusguardian.com",),
        ).fetchone()
        if not admin_exists:
            connection.execute(
                "INSERT INTO users (name, email, password, role, created_at) VALUES (?, ?, ?, ?, ?)",
                ("Campus Admin", "admin@campusguardian.com", hash_password("admin123"), "admin", now),
            )

        connection.commit()

    except sqlite3.Error:
        connection.rollback()
        raise
    finally:
        connection.close()


def login_user(email, password):



    connection = get_connection()



    user = connection.execute(

        """

        SELECT *

        FROM users

        WHERE lower(email)=lower(?)

        """,

        (email.strip(),)

    ).fetchone()



    connection.close()



    if user is None:

        return None



    if hash_password(password) == user["password"]:

        return dict(user)



    return None





def create_account(name, email, password):



    if not name or not email or not password:

        return False, "Please fill all fields."



    if len(password) < 6:

        return False, "Password must contain at least 6 characters."



    try:



        connection = get_connection()



        connection.execute(

            """

            INSERT INTO users

            (name,email,password,role,created_at)

            VALUES (?,?,?,?,?)

            """,

            (

                name.strip(),

                email.strip().lower(),

                hash_password(password),

                "user",

                datetime.now().strftime(

                    "%Y-%m-%d %H:%M:%S"

                )

            )

        )



        connection.commit()

        connection.close()



        return True, "Account created successfully."



    except sqlite3.IntegrityError:



        return False, "This email already exists."





# ============================================================

# AI RISK ANALYSIS

# ============================================================



def calculate_risk(category, description):



    text = (

        category + " " + description

    ).lower()



    critical_words = [

        "weapon",

        "gun",

        "bomb",

        "shooting",

        "fire",

        "explosion",

        "hostage",

        "death"

    ]



    high_words = [

        "fight",

        "fighting",

        "assault",

        "harassment",

        "stalking",

        "theft",

        "violence",

        "threat",

        "injury",

        "accident",

        "danger"

    ]



    medium_words = [

        "unsafe",

        "suspicious",

        "bullying",

        "damage",

        "leak",

        "pothole",

        "broken",

        "dark"

    ]



    if any(word in text for word in critical_words):

        return "Critical"



    if any(word in text for word in high_words):

        return "High"



    if any(word in text for word in medium_words):

        return "Medium"



    if category in [

        "Fire",

        "Medical Emergency",

        "Security Threat",

        "Fighting",

        "Lift"

    ]:

        return "High"



    return "Low"





def explain_risk(risk):



    explanations = {



        "Critical":

        "The report contains strong emergency indicators. "

        "Immediate human verification and emergency response are recommended.",



        "High":

        "The report contains serious safety indicators. "

        "Campus security or the responsible department should respond quickly.",



        "Medium":

        "The report contains potential safety concerns. "

        "The responsible department should investigate the issue.",



        "Low":

        "No strong emergency indicators were detected. "

        "The issue can be handled through normal campus procedures."

    }



    return explanations.get(

        risk,

        "Risk could not be determined."

    )






def build_ai_summary(incident):
    """Create a transparent, data-driven operational summary for an incident."""
    category = str(incident.get("category", "Other"))
    risk = str(incident.get("risk", "Low"))
    status = str(incident.get("status", "Open"))
    department = str(incident.get("department", "Campus Security"))
    location = str(incident.get("location", CAMPUS_ADDRESS))
    description = str(incident.get("description", "")).strip() or "No detailed description was provided."
    photo = bool(str(incident.get("photo_path", "")).strip())
    action_map = {
        "Critical": "Immediate human verification and emergency response are recommended.",
        "High": "Prioritize this case and dispatch the assigned department quickly.",
        "Medium": "Investigate promptly and monitor for escalation or repeat reports.",
        "Low": "Handle through normal campus procedures and monitor for recurrence.",
    }
    action = action_map.get(risk, action_map["Low"])
    evidence = "Photo evidence is attached." if photo else "No photo evidence is attached."
    return (f"**What happened:** {category} reported at {location}. Description: {description}\n\n"
            f"**Risk assessment:** {risk}. Current status is {status}.\n\n"
            f"**Response:** Route to **{department}**. {action}\n\n**Evidence:** {evidence}")


def calculate_campus_safety_score(df):
    """Return a 0-100 operational safety score; higher means safer."""
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
    score -= min(30, high * 6)
    score -= min(20, critical * 5)
    score -= min(20, active * 2)
    score -= min(15, recent * 1.5)
    score += min(10, (resolved / max(total, 1)) * 10)
    return int(max(0, min(100, round(score))))


def safety_score_label(score):
    if score >= 85:
        return "🟢 Excellent", "Campus conditions are relatively stable. Continue preventive monitoring."
    if score >= 70:
        return "🟡 Good", "Some safety concerns are active. Continue monitoring high-risk areas."
    if score >= 50:
        return "🟠 Needs Attention", "Several safety indicators require active administrative follow-up."
    return "🔴 Critical Attention", "High-risk or unresolved activity is elevated. Immediate review is recommended."


def generate_safety_insight(df):
    """Generate a concise trend insight from recent incident data."""
    if df is None or df.empty:
        return "No incident history is available yet. Submit reports to activate safety intelligence."
    created = pd.to_datetime(df["created_at"], errors="coerce")
    now = pd.Timestamp.now()
    last7 = int((created >= now - pd.Timedelta(days=7)).sum())
    previous7 = int(((created >= now - pd.Timedelta(days=14)) & (created < now - pd.Timedelta(days=7))).sum())
    counts = df["location"].astype(str).value_counts()
    top_location = counts.index[0] if not counts.empty else CAMPUS_ADDRESS
    top_count = int(counts.iloc[0]) if not counts.empty else 0
    high = int(df["risk"].isin(["High", "Critical"]).sum())
    unresolved = int((df["status"] != "Resolved").sum())
    if previous7 > 0 and last7 > previous7:
        trend = f"Incident activity increased from {previous7} to {last7} in the latest 7-day period."
    elif previous7 > 0 and last7 < previous7:
        trend = f"Incident activity decreased from {previous7} to {last7} in the latest 7-day period."
    else:
        trend = f"There are {last7} incident(s) in the latest 7-day period."
    priority = f"{high} high/critical incident(s) are present." if high else "No high/critical incidents are currently recorded."
    return (f"{trend} The most frequently reported location is **{top_location}** with {top_count} incident(s). "
            f"{priority} {unresolved} incident(s) remain active. "
            "This is a data-driven safety insight, not a guaranteed prediction of future incidents.")


def render_campus_heatmap(df, title="🔥 Campus Safety Heatmap"):
    """Render a Plotly density heatmap with a safe point-map fallback."""
    if df is None or df.empty:
        st.info("No GPS incidents are available for the heatmap.")
        return
    work = df.copy()
    for col in ["latitude", "longitude"]:
        if col not in work.columns:
            work[col] = pd.NA
        work[col] = pd.to_numeric(work[col], errors="coerce")
    work = work.dropna(subset=["latitude", "longitude"]).copy()
    work = work[work["latitude"].between(-90, 90) & work["longitude"].between(-180, 180)]
    work = work[~((work["latitude"] == 0) & (work["longitude"] == 0))]
    if work.empty:
        st.info("No valid GPS coordinates are available for the heatmap.")
        return
    weights = {"Critical":5,"High":4,"Medium":2,"Low":1}
    work["weight"] = work["risk"].map(weights).fillna(1)
    try:
        fig = go.Figure(go.Densitymapbox(lat=work["latitude"], lon=work["longitude"], z=work["weight"], radius=28, colorscale="Turbo", showscale=True, colorbar=dict(title="Risk Weight")))
        fig.update_layout(title=title, mapbox=dict(style="open-street-map", center={"lat":CAMPUS_LATITUDE,"lon":CAMPUS_LONGITUDE}, zoom=14), height=520, margin=dict(l=0,r=0,t=50,b=0))
        st.plotly_chart(fig, use_container_width=True)
    except Exception:
        st.map(work[["latitude","longitude"]], use_container_width=True)
        st.caption("Heatmap renderer unavailable; showing incident points instead.")


def assign_department(category):



    departments = {



        "Security": "Campus Security",

        "Security Threat": "Campus Security",

        "Harassment": "Student Welfare",

        "Medical Emergency": "Medical Unit",

        "Fire": "Fire & Safety",

        "Infrastructure": "Maintenance",

        "Water Leakage": "Maintenance",

        "Pothole": "Maintenance",

        "Streetlight": "Electrical Maintenance",

        "Traffic": "Campus Traffic",

        "Lift": "Lift & Electrical Maintenance",

        "Fighting": "Campus Security",

        "Other": "Campus Administration"

    }



    return departments.get(

        category,

        "Campus Security"

    )





# ============================================================

# INCIDENT DATABASE FUNCTIONS

# ============================================================



def get_all_incidents():



    connection = get_connection()



    incidents = connection.execute(

        """

        SELECT

            incidents.*,

            COALESCE(users.name, 'Unknown Reporter') AS reporter

        FROM incidents

        JOIN users

        ON incidents.user_id = users.id

        ORDER BY incidents.id DESC

        """

    ).fetchall()



    connection.close()
    return [dict(row) for row in incidents]

def get_user_incidents(user_id):



    connection = get_connection()



    incidents = connection.execute(

        """

        SELECT *

        FROM incidents

        WHERE user_id=?

        ORDER BY id DESC

        """,

        (user_id,)

    ).fetchall()



    connection.close()
    return [dict(row) for row in incidents]

def add_notification(user_id, message):



    connection = get_connection()



    connection.execute(

        """

        INSERT INTO notifications

        (user_id,message,created_at)

        VALUES (?,?,?)

        """,

        (

            user_id,

            message,

            datetime.now().strftime(

                "%Y-%m-%d %H:%M:%S"

            )

        )

    )



    connection.commit()

    connection.close()






def notify_admins(message):
    """Send an in-app notification to every administrator."""
    connection = get_connection()
    try:
        admins = connection.execute(
            "SELECT id FROM users WHERE role=?",
            ("admin",),
        ).fetchall()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        connection.executemany(
            "INSERT INTO notifications (user_id, message, created_at) VALUES (?, ?, ?)",
            [(row["id"], message, now) for row in admins],
        )
        connection.commit()
    finally:
        connection.close()


def get_incident_dataframe():
    """Return incidents as a pandas DataFrame with safe, predictable columns."""
    incidents = get_all_incidents()
    if not incidents:
        return pd.DataFrame()
    df = pd.DataFrame([dict(row) if isinstance(row, sqlite3.Row) else row for row in incidents])
    for col, default in {
        "location": "Unknown Location",
        "category": "Other",
        "risk": "Low",
        "status": "Open",
        "department": "Campus Security",
        "reporter": "Unknown Reporter",
        "created_at": "",
        "photo_path": "",
        "is_demo": 0,
    }.items():
        if col not in df.columns:
            df[col] = default
        df[col] = df[col].fillna(default)
    return df

# ============================================================

# LOGIN PAGE

# ============================================================



def login_page():

    # --------------------------------------------------------
    # PROFESSIONAL LOGIN SCREEN
    # Uses native Streamlit components for reliable rendering.
    # --------------------------------------------------------

    st.markdown("""
    <style>
        [data-testid="stAppViewContainer"] {
            background:
                radial-gradient(circle at 10% 15%, rgba(37,99,235,.20), transparent 32%),
                radial-gradient(circle at 90% 85%, rgba(6,182,212,.14), transparent 30%),
                #06101f;
        }

        [data-testid="stHeader"] { background: transparent; }
        #MainMenu, footer { visibility: hidden; }

        .block-container {
            max-width: 1220px;
            padding-top: 40px;
            padding-bottom: 30px;
        }

        .cg-brand {
            font-size: 25px;
            font-weight: 800;
            color: #f8fafc;
            margin-bottom: 2px;
        }

        .cg-brand-sub {
            font-size: 9px;
            font-weight: 800;
            letter-spacing: 2px;
            color: #64748b;
        }

        .cg-hero-title {
            font-size: 48px;
            line-height: 1.05;
            font-weight: 800;
            letter-spacing: -2px;
            color: #f8fafc;
            margin-top: 42px;
            margin-bottom: 18px;
        }

        .cg-hero-accent { color: #22d3ee; }

        .cg-eyebrow {
            color: #93c5fd;
            font-size: 11px;
            font-weight: 800;
            letter-spacing: 1.5px;
        }

        .cg-description {
            color: #94a3b8;
            font-size: 15px;
            line-height: 1.7;
            max-width: 570px;
        }

        .cg-feature-title {
            color: #e2e8f0;
            font-weight: 750;
            font-size: 14px;
        }

        .cg-feature-text {
            color: #64748b;
            font-size: 12px;
        }

        .cg-login-title {
            color: #f8fafc;
            font-size: 27px;
            font-weight: 800;
            margin-top: 20px;
        }

        .cg-login-sub {
            color: #64748b;
            font-size: 13px;
            margin-bottom: 18px;
        }

        div[data-baseweb="input"] {
            background: #0b1628 !important;
            border: 1px solid #243247 !important;
            border-radius: 11px !important;
        }

        div[data-baseweb="input"] input {
            color: #f8fafc !important;
        }

        label {
            color: #cbd5e1 !important;
            font-size: 12px !important;
            font-weight: 650 !important;
        }

        .stButton > button {
            border-radius: 11px !important;
            min-height: 46px !important;
            font-weight: 750 !important;
        }

        @media (max-width: 900px) {
            .cg-hero-title { font-size: 38px; }
        }
    </style>
    """, unsafe_allow_html=True)

    # Brand
    brand_col1, brand_col2 = st.columns([0.08, 0.92])
    with brand_col1:
        st.markdown("## 🛡️")
    with brand_col2:
        st.markdown('<div class="cg-brand">CampusGuardian AI</div>', unsafe_allow_html=True)
        st.markdown('<div class="cg-brand-sub">INTELLIGENT CAMPUS SAFETY PLATFORM</div>', unsafe_allow_html=True)

    left, right = st.columns([1.15, 0.85], gap="large")

    with left:
        st.markdown('<div class="cg-eyebrow">AI-POWERED SAFETY OPERATIONS</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="cg-hero-title">Safer campuses.<br><span class="cg-hero-accent">Smarter response.</span></div>',
            unsafe_allow_html=True
        )
        st.markdown(
            '<div class="cg-description">CampusGuardian AI turns campus safety reports into intelligent, actionable information — helping teams identify risk, prioritize incidents and respond faster.</div>',
            unsafe_allow_html=True
        )

        features = [
            ("🤖", "AI Risk Intelligence", "Automatically assess incident severity and explain why."),
            ("🚨", "Smart Incident Response", "Route reports to the appropriate campus department."),
            ("🔥", "Campus Hotspot Intelligence", "Detect locations where safety incidents are concentrated."),
            ("📊", "Safety Analytics", "Convert incident data into useful safety insights."),
        ]

        for icon, title, description in features:
            c1, c2 = st.columns([0.10, 0.90])
            with c1:
                st.markdown(f"### {icon}")
            with c2:
                st.markdown(f'<div class="cg-feature-title">{title}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="cg-feature-text">{description}</div>', unsafe_allow_html=True)

    with right:
        st.markdown('<div class="cg-login-title">Welcome back</div>', unsafe_allow_html=True)
        st.markdown('<div class="cg-login-sub">Sign in to your CampusGuardian safety workspace.</div>', unsafe_allow_html=True)

        login_tab, signup_tab = st.tabs(["🔐 Sign In", "📝 Create Account"])

        with login_tab:
            email = st.text_input(
                "Email address",
                placeholder="you@campus.edu",
                key="login_email"
            )

            password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter your password",
                key="login_password"
            )

            if st.button(
                "Sign in securely  →",
                type="primary",
                use_container_width=True,
                key="professional_sign_in"
            ):
                if not email.strip() or not password:
                    st.error("Please enter your email address and password.")
                else:
                    user = login_user(email, password)
                    if user:
                        st.session_state.logged_in = True
                        st.session_state.user = user
                        if user["role"] == "admin":
                            st.session_state.page = "📊 Overview"
                        else:
                            st.session_state.page = "🏠 Dashboard"
                        st.rerun()
                    else:
                        st.error("Invalid email or password.")

            st.success("CampusGuardian security systems operational")

            with st.expander("Demo access"):
                st.info("Student: student@campusguardian.com / student123")
                st.info("Admin: admin@campusguardian.com / admin123")

        with signup_tab:
            name = st.text_input(
                "Full Name",
                placeholder="Enter your full name",
                key="signup_name"
            )
            signup_email = st.text_input(
                "Email",
                placeholder="Enter your email",
                key="signup_email"
            )
            signup_password = st.text_input(
                "Password",
                type="password",
                placeholder="At least 6 characters",
                key="signup_password"
            )
            confirm = st.text_input(
                "Confirm Password",
                type="password",
                placeholder="Re-enter your password",
                key="signup_confirm"
            )

            if st.button(
                "Create account",
                use_container_width=True,
                key="professional_create_account"
            ):
                if signup_password != confirm:
                    st.error("Passwords do not match.")
                else:
                    success, message = create_account(
                        name,
                        signup_email,
                        signup_password
                    )
                    if success:
                        st.success(message)
                    else:
                        st.error(message)

            st.info("Account data is stored securely in the CampusGuardian database.")

    st.markdown(
        "<div style='text-align:center;color:#475569;font-size:10px;margin-top:35px;'>CampusGuardian AI · Intelligent Campus Safety & Incident Response<br>Secure • Intelligent • Responsive</div>",
        unsafe_allow_html=True
    )

# ============================================================

# SIDEBAR

# ============================================================



def show_sidebar(user):



    with st.sidebar:



        st.title("🛡️ CampusGuardian")



        st.caption(

            "SMART CAMPUS SAFETY"

        )



        st.divider()



        if user["role"] == "admin":



            pages = [

                "📊 Overview",

                "🚨 Incident Management",

                "👥 User Management",

                "🤖 AI Risk Analysis",

                "🗺️ Incident Map",

                "🔥 Hotspot Detection",

                "📈 Analytics",

                "🔔 Alerts",

                "🎬 Demo Mode",

                "⚙️ Settings"

            ]



        else:



            pages = [

                "🏠 Dashboard",

                "🚨 Report Incident",

                "📋 My Reports",

                "📍 Safety Map",

                "🔥 Hotspot Detection",

                "🆘 Emergency",

                "🔔 Notifications",

                "👤 Profile"

            ]



        page = st.radio(

            "Navigation",

            pages

        )



        st.divider()



        st.write(

            f"👤 **{user['name']}**"

        )



        st.caption(

            user["role"].upper()

        )



        if st.button(

            "🚪 Sign Out",

            use_container_width=True

        ):



            st.session_state.clear()

            st.rerun()



    return page





# ============================================================

# STUDENT DASHBOARD

# ============================================================



def dashboard(user):



    incidents = get_user_incidents(

        user["id"]

    )



    df = pd.DataFrame([dict(row) if isinstance(row, sqlite3.Row) else row for row in incidents])



    total = len(incidents)



    active = 0

    high = 0

    resolved = 0



    if not df.empty:



        active = int(

            (df["status"] != "Resolved").sum()

        )



        high = int(

            df["risk"].isin(

                ["High", "Critical"]

            ).sum()

        )



        resolved = int(

            (df["status"] == "Resolved").sum()

        )



    st.title(

        f"Welcome back, {user['name']} 👋"

    )



    st.caption(

        "Campus safety monitoring dashboard"

    )



    a, b, c, d = st.columns(4)



    a.metric(

        "My Reports",

        total

    )



    b.metric(

        "Active",

        active

    )



    c.metric(

        "High Risk",

        high

    )



    d.metric(

        "Resolved",

        resolved

    )



    st.divider()



    st.subheader(

        "Quick Actions"

    )



    x, y = st.columns(2)



    with x:



        if st.button(

            "🚨 Report Incident",

            use_container_width=True

        ):



            st.session_state.page = (

                "🚨 Report Incident"

            )



            st.rerun()



    with y:



        if st.button(

            "🔥 View Hotspots",

            use_container_width=True

        ):



            st.session_state.page = (

                "🔥 Hotspot Detection"

            )



            st.rerun()





# ============================================================

# REPORT INCIDENT

# ============================================================



def report_incident(user):
    st.title("🚨 Report Incident")
    st.caption("Submit a campus safety issue for AI analysis.")

    st.info(
        f"📍 **{CAMPUS_NAME}**\n\n"
        f"{CAMPUS_ADDRESS}\n\n"
        f"Campus GPS: **{CAMPUS_LATITUDE:.6f}, {CAMPUS_LONGITUDE:.6f}**"
    )

    categories = [
        "Security", "Security Threat", "Harassment", "Medical Emergency",
        "Fire", "Infrastructure", "Water Leakage", "Pothole",
        "Streetlight", "Traffic", "Lift", "Fighting", "Other",
    ]

    with st.form("incident_form"):
        title = st.text_input("Incident Title *")
        category = st.selectbox(
            "Category *",
            categories,
            format_func=lambda value: {
                "Lift": "🛗 Lift",
                "Fighting": "🥊 Fighting",
                "Water Leakage": "💧 Water Leakage",
                "Fire": "🔥 Fire",
                "Medical Emergency": "🚑 Medical Emergency",
                "Security Threat": "🚨 Security Threat",
            }.get(value, value),
        )
        location = st.text_input(
            "Location *",
            value=CAMPUS_ADDRESS,
            help="Enter the specific campus place, such as Main Block Lift, Canteen, Hostel Gate, etc.",
        )
        description = st.text_area(
            "Description *",
            height=150,
            placeholder="Describe what happened and where it happened.",
        )

        use_campus_location = st.checkbox(
            "📍 Use Sapthagiri NPS University campus GPS",
            value=True,
        )

        col1, col2 = st.columns(2)
        with col1:
            latitude = st.number_input(
                "Latitude", min_value=-90.0, max_value=90.0,
                value=float(CAMPUS_LATITUDE), format="%.6f",
            )
        with col2:
            longitude = st.number_input(
                "Longitude", min_value=-180.0, max_value=180.0,
                value=float(CAMPUS_LONGITUDE), format="%.6f",
            )

        if use_campus_location:
            latitude = CAMPUS_LATITUDE
            longitude = CAMPUS_LONGITUDE
            st.caption(f"Using campus GPS: {CAMPUS_LATITUDE:.6f}, {CAMPUS_LONGITUDE:.6f}")

        photo = st.file_uploader("Incident Photo", type=["jpg", "jpeg", "png"])
        submit = st.form_submit_button(
            "🚨 Submit Incident", type="primary", use_container_width=True
        )

    if not submit:
        return

    if not title.strip() or not location.strip() or not description.strip():
        st.error("Please fill all required fields.")
        return

    latitude, longitude = float(latitude), float(longitude)
    if not (-90 <= latitude <= 90):
        st.error("Latitude must be between -90 and 90.")
        return
    if not (-180 <= longitude <= 180):
        st.error("Longitude must be between -180 and 180.")
        return

    risk = calculate_risk(category, description)
    why = explain_risk(risk)
    dept = assign_department(category)
    photo_path = ""

    if photo:
        safe_name = Path(photo.name).name
        filename = f"incident_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}_{safe_name}"
        photo_path = str(PHOTO_FOLDER / filename)
        try:
            with open(photo_path, "wb") as file:
                file.write(photo.getbuffer())
        except OSError as error:
            st.error(f"Could not save the incident photo: {error}")
            return

    connection = None
    try:
        connection = get_connection()
        cursor = connection.execute(
            """
            INSERT INTO incidents
            (user_id, title, category, description, location, latitude, longitude,
             risk, status, department, ai_why, photo_path, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user["id"], title.strip(), category, description.strip(), location.strip(),
                latitude, longitude, risk, "Open", dept, why, photo_path,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            ),
        )
        incident_id = cursor.lastrowid
        connection.commit()
    except sqlite3.Error as error:
        if connection is not None:
            connection.rollback()
        if photo_path:
            try:
                Path(photo_path).unlink(missing_ok=True)
            except OSError:
                pass
        st.error(f"Could not submit the incident: {error}")
        return
    finally:
        if connection is not None:
            connection.close()

    try:
        add_notification(
            user["id"],
            f"Incident #{incident_id} submitted. Risk: {risk}. Department: {dept}",
        )
        notify_admins(
            f"🚨 New incident #{incident_id}: {category} reported by {user['name']}. Risk: {risk}. Department: {dept}."
        )
    except sqlite3.Error:
        pass

    st.success(f"Incident #{incident_id} submitted successfully!")
    c1, c2, c3 = st.columns(3)
    c1.metric("AI Risk", risk)
    c2.metric("Department", dept)
    c3.metric("GPS", f"{latitude:.6f}, {longitude:.6f}")
    st.write("### 📍 Incident Location")
    st.write(location.strip())
    st.write("### Why this risk?")
    st.write(why)
    photo_file = resolve_incident_photo(photo_path)
    if photo_file is not None:
        st.image(str(photo_file), width=400)

# ============================================================

# MY REPORTS

# ============================================================



def my_reports(user):



    st.title(

        "📋 My Reports"

    )



    incidents = get_user_incidents(

        user["id"]

    )



    if not incidents:



        st.info(

            "You have not submitted any incidents yet."

        )



        return



    for incident in incidents:



        with st.expander(

            f"#{incident['id']} - {incident['title']}"

        ):



            st.write(

                f"**Category:** {incident['category']}"

            )



            st.write(

                f"**Location:** {incident['location']}"

            )



            st.write(

                f"**Risk:** {incident['risk']}"

            )



            st.write(

                f"**Status:** {incident['status']}"

            )



            st.write(

                f"**Department:** {incident['department']}"

            )



            st.write(

                incident["description"]

            )



            st.write(

                "### 🤖 AI Explanation"

            )



            st.write(

                incident["ai_why"]

            )



            if incident["photo_path"]:



                if Path(

                    incident["photo_path"]

                ).exists():



                    st.image(

                        incident["photo_path"],

                        width=400

                    )





# ============================================================

# HOTSPOTS

# ============================================================



def hotspots():
    st.title("🔥 Campus Hotspot Intelligence")
    st.caption(f"Smart location analysis for {CAMPUS_NAME}. Hotspots combine volume, severity, recency and unresolved activity.")
    df = get_incident_dataframe()
    if df.empty:
        st.info("No incident data available. Submit reports or use Admin → Demo Mode to activate hotspot intelligence.")
        return
    df["created_dt"] = pd.to_datetime(df["created_at"], errors="coerce")
    now = pd.Timestamp.now()
    df["days_old"] = ((now-df["created_dt"]).dt.total_seconds()/86400).clip(lower=0).fillna(999)
    df["severity_score"] = df["risk"].map({"Critical":5,"High":4,"Medium":2,"Low":1}).fillna(1)
    df["recency_score"] = df["days_old"].apply(lambda d: 3 if d<=1 else (2 if d<=7 else (1 if d<=30 else 0)))
    grouped=df.groupby("location",dropna=False).agg(Incidents=("id","count"),Severity=("severity_score","sum"),Recent=("recency_score","sum"),High_Risk=("risk",lambda s:int(s.isin(["High","Critical"]).sum())),Active=("status",lambda s:int((s!="Resolved").sum()))).reset_index()
    raw=grouped["Incidents"]*3+grouped["Severity"]*2+grouped["Recent"]*2+grouped["High_Risk"]*3+grouped["Active"]
    max_raw=float(raw.max()) if not raw.empty else 0
    grouped["Hotspot Score"]=raw.round(0).astype(int)
    grouped["Score / 100"]=raw.apply(lambda x:round((x/max_raw)*100) if max_raw else 0)
    grouped["Risk Level"]=grouped["Score / 100"].apply(lambda x:"Critical" if x>=80 else ("High" if x>=60 else ("Medium" if x>=30 else "Low")))
    grouped=grouped.sort_values(["Score / 100","Incidents"],ascending=False)
    active_hotspots=int((grouped["Score / 100"]>=60).sum())
    high_risk=int(df["risk"].isin(["High","Critical"]).sum())
    score=calculate_campus_safety_score(df); label,help_text=safety_score_label(score)
    a,b,c,d,e=st.columns(5)
    a.metric("📌 Total Incidents",len(df)); b.metric("📍 Locations",grouped.shape[0]); c.metric("🔴 High/Critical",high_risk); d.metric("🔥 Active Hotspots",active_hotspots); e.metric("🛡️ Safety Score",f"{score}/100")
    st.progress(score/100,text=f"Campus Safety Score · {label}"); st.caption(help_text)
    st.divider()
    st.subheader("🔥 Smart Hotspot Ranking")
    st.caption("Higher scores indicate greater concentration of incidents, severity, recent activity and unresolved cases.")
    chart_df=grouped.head(10).sort_values("Score / 100",ascending=True)
    fig=px.bar(chart_df,x="Score / 100",y="location",orientation="h",text="Score / 100",title="Top Campus Hotspots"); fig.update_traces(textposition="outside"); fig.update_layout(xaxis_title="Hotspot Score / 100",yaxis_title="Location",xaxis_range=[0,max(100,int(chart_df["Score / 100"].max())+15)]); st.plotly_chart(fig,use_container_width=True)
    st.subheader("🗺️ Campus Risk Heatmap")
    render_campus_heatmap(df,"CampusGuardian · Incident Risk Concentration")
    st.subheader("📊 Hotspot Risk Breakdown")
    c1,c2=st.columns(2)
    with c1:
        risk_fig=px.bar(grouped.head(10),x="location",y=["Incidents","High_Risk","Active"],barmode="group",title="Volume vs High-Risk vs Active"); st.plotly_chart(risk_fig,use_container_width=True)
    with c2:
        category=df["category"].value_counts().reset_index(); category.columns=["Category","Incidents"]; st.plotly_chart(px.pie(category,names="Category",values="Incidents",hole=.45,title="Incident Category Mix"),use_container_width=True)
    st.subheader("📍 Hotspot Details")
    st.dataframe(grouped[["location","Incidents","High_Risk","Active","Recent","Score / 100","Risk Level"]],use_container_width=True,hide_index=True)
    st.subheader("🤖 AI Safety Insight")
    st.info(generate_safety_insight(df))
    if not grouped.empty:
        top=grouped.iloc[0]; icon={"Critical":"🔴","High":"🔴","Medium":"🟠","Low":"🟢"}.get(top["Risk Level"],"⚪")
        st.markdown(f"### {icon} Highest-Priority Location: **{top['location']}**")
        st.write(f"**Hotspot Score:** {int(top['Score / 100'])}/100 · **{int(top['Incidents'])} incidents** · **{int(top['High_Risk'])} high/critical** · **{int(top['Active'])} active**")
        if top["Risk Level"] in ["Critical","High"]: st.error("Recommended action: increase security/maintenance monitoring at this location and review active incidents in Incident Management.")
        else: st.success("Recommended action: continue monitoring this location for repeated incidents.")

# ============================================================

# SAFETY MAP

# ============================================================



def safety_map(user):

    st.title("📍 Safety Map")
    st.caption(f"Campus reference: {CAMPUS_ADDRESS} | GPS {CAMPUS_LATITUDE:.6f}, {CAMPUS_LONGITUDE:.6f}")

    incidents = get_user_incidents(user["id"])

    if not incidents:
        st.info("No incidents available yet.")
        return

    df = pd.DataFrame([dict(row) if isinstance(row, sqlite3.Row) else row for row in incidents])

    for column in ["latitude", "longitude"]:
        if column not in df.columns:
            df[column] = pd.NA

    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")

    df = df.dropna(subset=["latitude", "longitude"]).copy()
    df = df[
        df["latitude"].between(-90, 90)
        & df["longitude"].between(-180, 180)
        & ~((df["latitude"] == 0) & (df["longitude"] == 0))
    ].copy()

    if df.empty:
        st.info(
            "No valid coordinates are available. Enter latitude and longitude "
            "when submitting an incident to show it on the map."
        )
        return

    st.map(df[["latitude", "longitude"]], use_container_width=True)

    display_columns = [
        c for c in [
            "id", "title", "category", "location", "latitude", "longitude",
            "risk", "status", "department", "created_at"
        ] if c in df.columns
    ]
    st.subheader("📌 Mapped Incidents")
    st.dataframe(df[display_columns], use_container_width=True, hide_index=True)
# ============================================================

# EMERGENCY

# ============================================================



def emergency(user):
    st.title("🆘 Emergency Response")
    st.error("For immediate danger in India, call **112**. CampusGuardian can also create a Critical incident for campus administrators.")

    st.markdown("### 🚨 Emergency SOS")
    st.write("Use SOS when there is an immediate safety threat such as violence, fire, serious injury or another critical emergency.")

    st.info(f"📍 Emergency location defaults to {CAMPUS_NAME}: {CAMPUS_LATITUDE:.6f}, {CAMPUS_LONGITUDE:.6f}")

    emergency_type = st.selectbox("Emergency Type", ["Medical Emergency","Fire","Fighting","Security Threat","Other Critical Emergency"])
    emergency_note = st.text_area("What is happening?", placeholder="Briefly describe the emergency and where it is happening.")
    confirm = st.checkbox("I confirm this is a genuine emergency.")

    if st.button("🚨 SEND EMERGENCY SOS", type="primary", use_container_width=True):
        if not confirm:
            st.warning("Please confirm that this is a genuine emergency before sending SOS.")
            return
        description = emergency_note.strip() or f"Emergency SOS triggered by user: {user['name']}"
        connection = get_connection()
        try:
            cur = connection.execute(
                """INSERT INTO incidents\n                (user_id,title,category,description,location,latitude,longitude,risk,status,department,ai_why,photo_path,admin_note,created_at)\n                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (user["id"], f"🚨 EMERGENCY SOS - {emergency_type}", emergency_type, description, CAMPUS_ADDRESS, CAMPUS_LATITUDE, CAMPUS_LONGITUDE, "Critical", "Open", "Campus Security", "Emergency SOS automatically classified as Critical for immediate administrative response.", "", "SOS generated from Emergency Response.", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            )
            incident_id = cur.lastrowid
            connection.commit()
        finally:
            connection.close()
        add_notification(user["id"], f"🚨 Emergency SOS #{incident_id} created. Campus Security has been notified.")
        try:
            notify_admins(f"🚨 CRITICAL EMERGENCY #{incident_id}: {emergency_type} reported by {user['name']}.")
        except sqlite3.Error:
            pass
        st.error(f"Emergency #{incident_id} created as CRITICAL. Contact campus security / 112 immediately if needed.")
        st.success("Campus administrators have been notified.")

# ============================================================

# NOTIFICATIONS

# ============================================================



def notifications(user):
    st.title("🔔 Notifications")
    st.caption("Safety events, incident updates and emergency alerts.")

    connection = get_connection()
    rows = connection.execute("SELECT * FROM notifications WHERE user_id=? ORDER BY id DESC", (user["id"],)).fetchall()
    connection.close()
    notifications_data = [dict(row) for row in rows]

    if not notifications_data:
        st.success("🟢 No new notifications.")
        return

    for item in notifications_data:
        message = item["message"]
        icon = "🚨" if "Critical" in message or "EMERGENCY" in message.upper() else ("✅" if "resolved" in message.lower() else "🔔")
        st.info(f"{icon} **{message}**\n\n🕐 {item['created_at']}")

# ============================================================

# PROFILE

# ============================================================



def profile(user):



    st.title(

        "👤 Profile"

    )



    st.write(

        f"**Name:** {user['name']}"

    )



    st.write(

        f"**Email:** {user['email']}"

    )



    st.write(

        f"**Account Type:** {user['role']}"

    )



    st.write(

        f"**Created:** {user['created_at']}"

    )





# ============================================================

# ADMIN OVERVIEW

# ============================================================



def admin_overview():
    st.title("🛡️ CampusGuardian Safety Command Center")
    st.caption(f"Real-time safety operations, evidence review and preventive intelligence for {CAMPUS_NAME}")
    df=get_incident_dataframe()
    if df.empty:
        st.info("No incidents have been reported yet."); st.caption("Use **Demo Mode** to populate realistic hackathon demonstration data."); return
    for col in ["risk","status","category","department"]: df[col]=df[col].astype(str)
    df["created_dt"]=pd.to_datetime(df["created_at"],errors="coerce")
    total=len(df); critical=int((df["risk"]=="Critical").sum()); high=int(df["risk"].isin(["High","Critical"]).sum()); active=int((df["status"]!="Resolved").sum()); resolved=int((df["status"]=="Resolved").sum()); recent=int((df["created_dt"]>=pd.Timestamp.now()-pd.Timedelta(days=7)).sum()); resolution_rate=round(resolved/max(total,1)*100,1); safety_score=calculate_campus_safety_score(df); label,help_text=safety_score_label(safety_score)
    a,b,c,d,e,f=st.columns(6); a.metric("📌 Total",total); b.metric("🔴 High/Critical",high); c.metric("🚨 Active",active); d.metric("✅ Resolved",resolved); e.metric("🕐 7 Days",recent); f.metric("🛡️ Safety Score",f"{safety_score}/100")
    st.progress(safety_score/100,text=f"{label} · {help_text}")
    if critical: st.error(f"🚨 {critical} Critical incident(s) require immediate human attention.")
    elif high: st.warning(f"⚠️ {high} high-priority incident(s) require attention.")
    else: st.success("🟢 No active high-risk incidents require immediate attention.")
    st.divider()
    c1,c2=st.columns([1.6,1])
    with c1:
        st.subheader("🤖 AI Safety Insight"); st.info(generate_safety_insight(df))
    with c2:
        st.subheader("📊 Resolution Health"); st.metric("Resolution Rate",f"{resolution_rate}%"); st.caption("Higher resolution rate indicates stronger response completion.")
    left,right=st.columns(2)
    with left:
        risk_counts=df["risk"].value_counts().reindex(["Critical","High","Medium","Low"],fill_value=0).reset_index(); risk_counts.columns=["Risk","Count"]; fig=px.bar(risk_counts,x="Risk",y="Count",title="🚨 Risk Distribution",text="Count"); fig.update_traces(textposition="outside"); st.plotly_chart(fig,use_container_width=True)
    with right:
        status_counts=df["status"].value_counts().reset_index(); status_counts.columns=["Status","Count"]; st.plotly_chart(px.pie(status_counts,names="Status",values="Count",hole=.45,title="📌 Incident Status"),use_container_width=True)
    st.subheader("📈 Recent Incident Trend")
    daily=df.dropna(subset=["created_dt"]).copy()
    if not daily.empty:
        daily["Date"]=daily["created_dt"].dt.date; trend=daily.groupby("Date").size().reset_index(name="Incidents"); st.plotly_chart(px.line(trend,x="Date",y="Incidents",markers=True,title="Incidents Over Time"),use_container_width=True)
    st.subheader("🔥 Top Campus Hotspots")
    hotspot=df.groupby("location",as_index=False).size().rename(columns={"size":"Incidents"}).sort_values("Incidents",ascending=False).head(5)
    if not hotspot.empty:
        hfig=px.bar(hotspot,x="Incidents",y="location",orientation="h",text="Incidents",title="Most Reported Locations"); hfig.update_traces(textposition="outside"); st.plotly_chart(hfig,use_container_width=True)
    st.subheader("🗺️ Campus Risk Heatmap"); render_campus_heatmap(df,"Admin Command Center · Risk Concentration")
    st.subheader("🚨 Active Incidents Requiring Attention")
    active_df=df[df["status"]!="Resolved"].copy(); active_df["priority"]=active_df["risk"].map({"Critical":4,"High":3,"Medium":2,"Low":1}).fillna(0); active_df=active_df.sort_values(["priority","created_dt"],ascending=[False,False]); display=[c for c in ["id","title","category","risk","status","department","location","reporter","created_at"] if c in active_df.columns]; st.dataframe(active_df[display].head(12),use_container_width=True,hide_index=True)
    st.caption("Use **Incident Management** to view evidence, read the AI summary, assign a department and move incidents through Open → Assigned → In Progress → Resolved.")

# ============================================================

# INCIDENT MANAGEMENT

# ============================================================



def incident_management():
    st.title("🚨 Incident Management")
    st.caption("Admin response center — review evidence, assign teams, update status and document resolution.")

    df = get_incident_dataframe()
    if df.empty:
        st.info("No incidents have been reported yet.")
        return

    f1, f2, f3, f4 = st.columns(4)
    risk_filter = f1.selectbox("Risk", ["All","Critical","High","Medium","Low"])
    status_filter = f2.selectbox("Status", ["All","Open","Assigned","In Progress","Resolved"])
    category_filter = f3.selectbox("Category", ["All"] + sorted(df["category"].astype(str).unique().tolist()))
    search = f4.text_input("Search", placeholder="title, location, reporter...")

    filtered = df.copy()
    if risk_filter != "All":
        filtered = filtered[filtered["risk"] == risk_filter]
    if status_filter != "All":
        filtered = filtered[filtered["status"] == status_filter]
    if category_filter != "All":
        filtered = filtered[filtered["category"] == category_filter]
    if search.strip():
        q = search.strip().lower()
        mask = filtered.apply(lambda row: q in " ".join(str(row.get(c,"")) for c in ["title","location","reporter","description"]).lower(), axis=1)
        filtered = filtered[mask]

    st.info(f"Showing **{len(filtered)}** incident(s) out of **{len(df)}**.")

    if filtered.empty:
        st.warning("No incidents match the selected filters.")
        return

    for incident in filtered.to_dict("records"):
        risk_icon = {"Critical":"🔴","High":"🔴","Medium":"🟠","Low":"🟢"}.get(incident["risk"],"⚪")
        with st.expander(f"{risk_icon} #{incident['id']} · {incident['title']} · {incident['risk']} · {incident['status']}"):
            top = st.columns([1.3,1,1,1])
            top[0].metric("Risk", incident["risk"])
            top[1].metric("Status", incident["status"])
            top[2].metric("Department", incident["department"])
            top[3].metric("Reporter", incident["reporter"])

            detail_left, detail_right = st.columns([1.15,1])
            with detail_left:
                st.markdown("### 📋 Incident Details")
                st.write(f"**Category:** {incident['category']}")
                st.write(f"**Location:** {incident['location']}")
                st.write(f"**Reported:** {incident['created_at']}")
                st.write(f"**Description:** {incident['description']}")
                if incident.get("ai_why"):
                    st.info(f"🤖 **AI Risk Explanation:** {incident['ai_why']}")
                st.markdown("### 🧠 AI Safety Summary")
                st.success(build_ai_summary(incident))
                if incident.get("admin_note"):
                    st.warning(f"📝 **Current Admin Note:** {incident['admin_note']}")

            with detail_right:
                st.markdown("### 📷 Evidence Photo")
                photo_value = incident.get("photo_path") or ""
                if photo_value:
                    photo_file = resolve_incident_photo(photo_value)
                    if photo_file:
                        st.image(str(photo_file), caption=f"Evidence · Incident #{incident['id']}", use_container_width=True)
                        try:
                            data = photo_file.read_bytes()
                            mime = "image/jpeg" if photo_file.suffix.lower() in [".jpg",".jpeg"] else "image/png"
                            st.download_button("⬇️ Download Evidence", data=data, file_name=photo_file.name, mime=mime, key=f"dl_{incident['id']}")
                        except OSError:
                            pass
                    else:
                        st.error(f"Photo record exists but file is missing: {photo_value}")
                else:
                    st.caption("No evidence photo attached.")

            st.divider()
            st.markdown("### ⚙️ Response Actions")
            status_options = ["Open","Assigned","In Progress","Resolved"]
            department_options = [
                "Campus Security","Maintenance","Lift & Electrical Maintenance","Electrical Maintenance",
                "Medical Unit","Fire & Safety","Student Welfare","Campus Traffic","Campus Administration"
            ]
            current_status = incident["status"] if incident["status"] in status_options else "Open"
            current_department = incident["department"] if incident["department"] in department_options else incident["department"]
            if current_department not in department_options:
                department_options.append(current_department)

            c1,c2 = st.columns(2)
            with c1:
                new_status = st.selectbox("Update Status", status_options, index=status_options.index(current_status), key=f"admin_status_{incident['id']}")
            with c2:
                new_department = st.selectbox("Assign Department", department_options, index=department_options.index(current_department), key=f"admin_dept_{incident['id']}")
            note = st.text_area("Admin Response Note", value=incident.get("admin_note") or "", key=f"admin_note_{incident['id']}", height=90)

            if st.button("💾 Save Response", type="primary", key=f"save_response_{incident['id']}", use_container_width=True):
                connection = get_connection()
                try:
                    connection.execute("UPDATE incidents SET status=?, department=?, admin_note=? WHERE id=?", (new_status,new_department,note.strip(),incident["id"]))
                    connection.commit()
                finally:
                    connection.close()

                add_notification(incident["user_id"], f"Incident #{incident['id']} updated: {new_status}. Department: {new_department}.")
                if new_status == "Resolved":
                    add_notification(incident["user_id"], f"✅ Incident #{incident['id']} has been resolved by CampusGuardian administration.")
                try:
                    notify_admins(f"Incident #{incident['id']} updated to {new_status} and assigned to {new_department}.")
                except sqlite3.Error:
                    pass
                st.success("Incident response saved.")
                st.rerun()

# ============================================================
# DEMO MODE
# ============================================================


def demo_mode():
    st.title("🎬 Hackathon Demo Mode")
    st.caption("Populate realistic, clearly-labelled demonstration incidents for your hackathon presentation.")

    df = get_incident_dataframe()
    demo_count = int(df["is_demo"].fillna(0).astype(int).sum()) if not df.empty else 0
    a, b, c = st.columns(3)
    a.metric("Demo Incidents", demo_count)
    b.metric("All Incidents", len(df))
    c.metric("Campus", CAMPUS_NAME)

    st.warning("Demo records are clearly marked as demonstration data. Do not present them as real incidents.")

    if st.button("▶️ Load Hackathon Demo Data", type="primary", use_container_width=True):
        connection = get_connection()
        try:
            student = connection.execute(
                "SELECT id FROM users WHERE email=?",
                ("student@campusguardian.com",),
            ).fetchone()
            user_id = int(student["id"]) if student else 1
            now = datetime.now()

            demo_rows = [
                ("Water Leakage near Main Block", "Water Leakage", "Water is leaking near a main corridor and may create a slip hazard.", "Main Block", CAMPUS_LATITUDE + .0012, CAMPUS_LONGITUDE + .0004, "Medium", "In Progress", "Maintenance"),
                ("Fighting reported near Block A", "Fighting", "Two students were reported fighting near Block A.", "Block A", CAMPUS_LATITUDE + .0006, CAMPUS_LONGITUDE - .0007, "High", "Open", "Campus Security"),
                ("Lift failure in Academic Block", "Lift", "Campus lift stopped between floors and requires technical inspection.", "Academic Block", CAMPUS_LATITUDE - .0008, CAMPUS_LONGITUDE + .0010, "High", "Assigned", "Lift & Electrical Maintenance"),
                ("Medical emergency at Sports Area", "Medical Emergency", "A student requires urgent medical assistance after an injury.", "Sports Area", CAMPUS_LATITUDE + .0018, CAMPUS_LONGITUDE + .0014, "High", "In Progress", "Medical Unit"),
                ("Fire alarm near Laboratory", "Fire", "Smoke/fire alarm reported near the laboratory area.", "Laboratory Block", CAMPUS_LATITUDE - .0010, CAMPUS_LONGITUDE - .0012, "Critical", "Open", "Fire & Safety"),
                ("Broken streetlight at Parking Area", "Streetlight", "A streetlight is not working near the parking area.", "Parking Area", CAMPUS_LATITUDE - .0017, CAMPUS_LONGITUDE + .0002, "Medium", "Resolved", "Electrical Maintenance"),
                ("Harassment concern near Library", "Harassment", "A student reported repeated harassment near the library entrance.", "Library Entrance", CAMPUS_LATITUDE + .0009, CAMPUS_LONGITUDE - .0011, "High", "Open", "Student Welfare"),
                ("Pothole near Campus Gate", "Pothole", "A pothole is creating a hazard for pedestrians and two-wheelers.", "Campus Gate", CAMPUS_LATITUDE - .0020, CAMPUS_LONGITUDE - .0004, "Medium", "Resolved", "Maintenance"),
                ("Suspicious activity at Hostel Gate", "Security Threat", "Suspicious activity was reported near the hostel gate.", "Hostel Gate", CAMPUS_LATITUDE + .0021, CAMPUS_LONGITUDE - .0002, "High", "Assigned", "Campus Security"),
                ("Traffic congestion at Main Gate", "Traffic", "Heavy traffic is causing congestion during peak campus entry time.", "Main Gate", CAMPUS_LATITUDE - .0014, CAMPUS_LONGITUDE + .0016, "Medium", "Open", "Campus Traffic"),
            ]

            for i, row in enumerate(demo_rows):
                title, category, description, location, lat, lon, risk, status, department = row
                created = (now - pd.Timedelta(days=i % 7, hours=i)).strftime("%Y-%m-%d %H:%M:%S")
                why = explain_risk(risk)
                connection.execute(
                    """INSERT INTO incidents
                    (user_id,title,category,description,location,latitude,longitude,risk,status,department,ai_why,photo_path,admin_note,is_demo,created_at)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (user_id, title, category, description, location, lat, lon, risk, status,
                     department, why, "", "Hackathon demo record", 1, created),
                )
            connection.commit()
        except sqlite3.Error as error:
            connection.rollback()
            st.error(f"Could not load demo data: {error}")
            return
        finally:
            connection.close()
        st.success(f"Loaded {len(demo_rows)} hackathon demo incidents successfully.")
        st.rerun()

    if st.button("🧹 Remove Demo Data", use_container_width=True):
        connection = get_connection()
        try:
            connection.execute("DELETE FROM incidents WHERE is_demo=1")
            connection.commit()
        except sqlite3.Error as error:
            connection.rollback()
            st.error(f"Could not remove demo data: {error}")
            return
        finally:
            connection.close()
        st.success("Demo incidents removed.")
        st.rerun()


def user_management():
    st.title("👥 User Management")
    st.caption("View registered CampusGuardian users and their roles.")
    connection = get_connection()
    try:
        rows = connection.execute(
            "SELECT id,name,email,role,created_at FROM users ORDER BY id DESC"
        ).fetchall()
    finally:
        connection.close()
    df = pd.DataFrame([dict(r) for r in rows])
    if df.empty:
        st.info("No users found.")
        return
    st.metric("Registered Users", len(df))
    st.dataframe(df, use_container_width=True, hide_index=True)


def ai_risk_analysis():
    st.title("🤖 AI Risk Analysis")
    st.caption("Transparent rule-based risk intelligence used by CampusGuardian.")
    df = get_incident_dataframe()
    if df.empty:
        st.info("No incidents available for analysis.")
        return
    risk_counts = df["risk"].value_counts().reindex(["Critical", "High", "Medium", "Low"], fill_value=0)
    cols = st.columns(4)
    for col, risk in zip(cols, risk_counts.index):
        col.metric(risk, int(risk_counts[risk]))
    st.divider()
    selected_id = st.selectbox("Select incident", df["id"].tolist())
    incident = next((x for x in get_all_incidents() if x["id"] == selected_id), None)
    if incident:
        st.subheader(f"#{incident['id']} · {incident['title']}")
        st.write(f"**Category:** {incident['category']}")
        st.write(f"**Description:** {incident['description']}")
        st.success(f"AI Risk: {incident['risk']}")
        st.info(incident.get("ai_why") or explain_risk(incident["risk"]))
        st.caption("AI risk is decision support, not a replacement for human emergency assessment.")


def analytics():
    st.title("📈 Analytics")
    df = get_incident_dataframe()
    if df.empty:
        st.info("No incident data available yet.")
        return
    df["created_dt"] = pd.to_datetime(df["created_at"], errors="coerce")
    left, right = st.columns(2)
    with left:
        category = df["category"].value_counts().reset_index()
        category.columns = ["Category", "Incidents"]
        st.plotly_chart(px.bar(category, x="Category", y="Incidents", title="Incidents by Category"), use_container_width=True)
    with right:
        risk = df["risk"].value_counts().reindex(["Critical", "High", "Medium", "Low"], fill_value=0).reset_index()
        risk.columns = ["Risk", "Incidents"]
        st.plotly_chart(px.pie(risk, names="Risk", values="Incidents", hole=.45, title="Risk Distribution"), use_container_width=True)
    trend = df.dropna(subset=["created_dt"]).copy()
    if not trend.empty:
        trend["Date"] = trend["created_dt"].dt.date
        trend = trend.groupby("Date").size().reset_index(name="Incidents")
        st.plotly_chart(px.line(trend, x="Date", y="Incidents", markers=True, title="Incident Trend"), use_container_width=True)
    st.download_button(
        "⬇️ Download Incident CSV",
        df.to_csv(index=False).encode("utf-8"),
        file_name="campusguardian_incidents.csv",
        mime="text/csv",
        use_container_width=True,
    )


def alerts():
    st.title("🔔 Alerts")
    st.caption("High-priority and unresolved incidents requiring attention.")
    df = get_incident_dataframe()
    if df.empty:
        st.success("No incidents available.")
        return
    alerts_df = df[df["risk"].isin(["Critical", "High"]) | (df["status"] != "Resolved")].copy()
    if alerts_df.empty:
        st.success("🟢 No active alerts.")
        return
    alerts_df["priority"] = alerts_df["risk"].map({"Critical": 4, "High": 3, "Medium": 2, "Low": 1}).fillna(0)
    alerts_df = alerts_df.sort_values(["priority", "id"], ascending=[False, False])
    for incident in alerts_df.to_dict("records"):
        icon = "🚨" if incident["risk"] == "Critical" else "⚠️"
        st.warning(f"{icon} **#{incident['id']} — {incident['title']}** · {incident['risk']} · {incident['status']} · {incident['department']}")


def settings():
    st.title("⚙️ Settings")
    st.caption("CampusGuardian configuration and system information.")
    st.info(f"**Campus:** {CAMPUS_NAME}\n\n**Address:** {CAMPUS_ADDRESS}\n\n**GPS:** {CAMPUS_LATITUDE:.6f}, {CAMPUS_LONGITUDE:.6f}")
    st.write("### System")
    st.write("• SQLite database enabled")
    st.write("• Incident photo storage enabled")
    st.write("• Rule-based AI risk scoring enabled")
    st.write("• Admin/user role separation enabled")
    st.write("• In-app notifications enabled")
    if st.button("🔄 Rebuild Database Indexes", use_container_width=True):
        connection = get_connection()
        try:
            connection.execute("CREATE INDEX IF NOT EXISTS idx_incidents_status ON incidents(status)")
            connection.execute("CREATE INDEX IF NOT EXISTS idx_incidents_risk ON incidents(risk)")
            connection.execute("CREATE INDEX IF NOT EXISTS idx_incidents_category ON incidents(category)")
            connection.execute("CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id)")
            connection.commit()
        finally:
            connection.close()
        st.success("Database indexes are healthy.")


def route_page(user, page):
    admin_routes = {
        "📊 Overview": admin_overview,
        "🚨 Incident Management": incident_management,
        "👥 User Management": user_management,
        "🤖 AI Risk Analysis": ai_risk_analysis,
        "🗺️ Incident Map": lambda: render_campus_heatmap(get_incident_dataframe(), "CampusGuardian · Incident Map"),
        "🔥 Hotspot Detection": hotspots,
        "📈 Analytics": analytics,
        "🔔 Alerts": alerts,
        "🎬 Demo Mode": demo_mode,
        "⚙️ Settings": settings,
    }
    user_routes = {
        "🏠 Dashboard": lambda: dashboard(user),
        "🚨 Report Incident": lambda: report_incident(user),
        "📋 My Reports": lambda: my_reports(user),
        "📍 Safety Map": lambda: safety_map(user),
        "🔥 Hotspot Detection": hotspots,
        "🆘 Emergency": lambda: emergency(user),
        "🔔 Notifications": lambda: notifications(user),
        "👤 Profile": lambda: profile(user),
    }
    routes = admin_routes if user["role"] == "admin" else user_routes
    handler = routes.get(page)
    if handler is None:
        st.error("Page not found. Please choose another page from the sidebar.")
        return
    handler()


# ============================================================
# APPLICATION ENTRY POINT
# ============================================================

initialize_database()

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user" not in st.session_state:
    st.session_state.user = None
if "page" not in st.session_state:
    st.session_state.page = "🏠 Dashboard"

if not st.session_state.logged_in or not st.session_state.user:
    login_page()
else:
    user = st.session_state.user
    page = show_sidebar(user)
    st.session_state.page = page
    route_page(user, page)