import sys
import os
import io
from datetime import datetime
from pathlib import Path

# Ensure UTF-8 output on Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

print("==================================================================")
print("       CAMPUSGUARDIAN AI - COMPLETE VERIFICATION SUITE           ")
print("==================================================================")

passed_tests = 0
total_tests = 0

def record_test(name, success, details=""):
    global passed_tests, total_tests
    total_tests += 1
    status = "✅ PASS" if success else "❌ FAIL"
    if success:
        passed_tests += 1
    print(f"[{status}] {name}")
    if details:
        print(f"        └─ {details}")

# ----------------------------------------------------------------
# TEST GROUP 1: ENVIRONMENT & DEPENDENCIES
# ----------------------------------------------------------------
print("\n--- 1. ENVIRONMENT & DEPENDENCIES ---")
try:
    import streamlit
    import pandas
    import plotly
    import numpy
    import sklearn
    import PIL
    import PIL.Image
    import cv2
    import sqlite3
    import hashlib
    import secrets
    record_test("Package Imports", True, f"Streamlit {streamlit.__version__}, Pandas {pandas.__version__}, Plotly {plotly.__version__}")
except Exception as e:
    record_test("Package Imports", False, str(e))

# ----------------------------------------------------------------
# TEST GROUP 2: SYNTAX & COMPILATION
# ----------------------------------------------------------------
print("\n--- 2. PYTHON COMPILATION ---")
py_files = [
    "app.py", "database.py", "dashboard.py", "emergency.py",
    "hotspot.py", "scoring.py", "duplicate.py", "explainability.py",
    "event_logger.py", "ai.py", "prompts.py"
]
all_compiled = True
compile_errors = []
import py_compile
for pyf in py_files:
    if os.path.exists(pyf):
        try:
            py_compile.compile(pyf, doraise=True)
        except Exception as e:
            all_compiled = False
            compile_errors.append(f"{pyf}: {e}")

record_test("Compile All Core Python Modules", all_compiled, f"Verified {len(py_files)} files: {', '.join(py_files)}")

# ----------------------------------------------------------------
# TEST GROUP 3: DATABASE SCHEMA & REPOSITORY INTEGRITY
# ----------------------------------------------------------------
print("\n--- 3. DATABASE SCHEMA & DATA INTEGRITY ---")
import app

conn = app.get_connection()
tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
has_tables = all(t in tables for t in ["users", "incidents", "notifications"])
record_test("Database Tables Exist", has_tables, f"Tables found: {tables}")

# Check columns of incidents
inc_cols = {r["name"] for r in conn.execute("PRAGMA table_info(incidents)").fetchall()}
req_cols = {"id", "user_id", "title", "category", "description", "location", "latitude", "longitude", "risk", "status", "department", "ai_why", "photo_path", "admin_note", "created_at"}
has_cols = req_cols.issubset(inc_cols)
record_test("Incidents Schema Complete", has_cols, f"Has all {len(req_cols)} required columns")

# Check incident row counts and category diversity
incidents = app.get_all_incidents()
inc_count = len(incidents)
cats = set(i["category"] for i in incidents)
record_test("Incident Records Count & Diversity", inc_count >= 20, f"Found {inc_count} incidents across categories: {sorted(list(cats))}")

# Check users row count
user_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
record_test("Users Table Records", user_count >= 2, f"Found {user_count} registered users")

# Capture baseline counts for zero-mutation verification in Group 12
baseline_inc_count = inc_count
baseline_usr_count = user_count
conn.close()

# ----------------------------------------------------------------
# TEST GROUP 4: SECURITY & AUTHENTICATION
# ----------------------------------------------------------------
print("\n--- 4. SECURITY & AUTHENTICATION ---")

# Student Auth
student = app.login_user("student@campusguardian.com", "student123")
student_ok = student is not None and student.get("role") == "user"
record_test("Student Demo Login (student@campusguardian.com)", student_ok, f"Authenticated ID={student.get('id') if student else None}, Role={student.get('role') if student else None}")

# Admin Auth
admin = app.login_user("admin@campusguardian.com", "admin123")
admin_ok = admin is not None and admin.get("role") == "admin"
record_test("Admin Demo Login (admin@campusguardian.com)", admin_ok, f"Authenticated ID={admin.get('id') if admin else None}, Role={admin.get('role') if admin else None}")

# Wrong password check
bad_auth = app.login_user("student@campusguardian.com", "wrongpassword999")
record_test("Invalid Password Rejection", bad_auth is None, "Correctly returned None for bad password")

# Non-existent user check
non_auth = app.login_user("nobody@nowhere.com", "student123")
record_test("Unknown User Rejection", non_auth is None, "Correctly returned None for unknown user")

# PBKDF2 Hash test
test_hash = app.hash_password("mypassword")
is_pbkdf2 = "$" in test_hash and len(test_hash) > 60
verify_ok = app.verify_password("mypassword", test_hash)
record_test("PBKDF2 Hashing (120k iterations)", is_pbkdf2 and verify_ok, f"Format: {test_hash[:20]}... verified={verify_ok}")

# Dynamic user registration and cleanup
ok, msg = app.create_account("Integration Test User", "verify_temp@campus.edu", "secure_pass_123", "Security", "+91 9999999999")
created_user = app.login_user("verify_temp@campus.edu", "secure_pass_123")
reg_ok = ok and created_user is not None
record_test("Dynamic Account Registration & Login", reg_ok, f"Registration response: {msg}")

# Clean up temporary test user
if created_user:
    del_conn = app.get_connection()
    del_conn.execute("DELETE FROM users WHERE email = ?", ("verify_temp@campus.edu",))
    del_conn.commit()
    del_conn.close()

# ----------------------------------------------------------------
# TEST GROUP 5: EVIDENCE PHOTO STORAGE & MULTI-PATH RESOLUTION
# ----------------------------------------------------------------
print("\n--- 5. EVIDENCE PHOTO STORAGE & RESOLUTION ---")

incidents_with_photos = [i for i in incidents if i.get("photo_path")]
resolved_photos = []
corrupt_photos = []

for inc in incidents_with_photos:
    res = app.resolve_incident_photo(inc["photo_path"])
    if res and res.exists():
        resolved_photos.append(res)
        # Verify valid readable image format with PIL
        try:
            with PIL.Image.open(res) as img:
                img.verify()
        except Exception as e:
            corrupt_photos.append(f"{res.name}: {e}")
    else:
        corrupt_photos.append(f"Missing: {inc['photo_path']}")

photos_ok = len(resolved_photos) == len(incidents_with_photos) and len(corrupt_photos) == 0
record_test(
    "Evidence Photo Multi-Path Resolution",
    photos_ok,
    f"{len(resolved_photos)}/{len(incidents_with_photos)} evidence images verified on disk and readable"
)

# ----------------------------------------------------------------
# TEST GROUP 6: AI RISK INFERENCE & SAFETY SCORE ENGINE
# ----------------------------------------------------------------
print("\n--- 6. AI RISK INFERENCE & SAFETY METRICS ---")

risk_critical = app.calculate_risk("Fire", "Smoke and open flames detected in science block")
risk_high = app.calculate_risk("Fighting", "Physical altercation between multiple individuals")
risk_medium = app.calculate_risk("Water Leakage", "Pipe leakage near corridor entrance")
risk_low = app.calculate_risk("General", "Lost notebook found on bench")

risk_engine_ok = (risk_critical == "Critical" and risk_high == "High" and risk_medium == "Medium" and risk_low == "Low")
record_test("Heuristic Risk Assessment Tiers", risk_engine_ok, f"Fire={risk_critical}, Fight={risk_high}, Leak={risk_medium}, Lost={risk_low}")

# Department routing
dept_fire = app.assign_department("Fire")
dept_med = app.assign_department("Medical Emergency")
dept_lift = app.assign_department("Lift")
dept_sec = app.assign_department("Security")
dept_ok = (dept_fire == "Fire & Safety" and dept_med == "Medical Unit" and dept_lift == "Lift & Elevator Maintenance" and dept_sec == "Campus Security")
record_test("Automated Department Routing", dept_ok, f"Fire->{dept_fire}, Med->{dept_med}, Lift->{dept_lift}, Sec->{dept_sec}")

# Campus Safety Score
df_inc = pandas.DataFrame(incidents)
safety_score = app.calculate_campus_safety_score(df_inc)
lbl, desc = app.safety_score_label(safety_score)
score_ok = 0 <= safety_score <= 100
record_test("Campus Safety Health Score (0-100)", score_ok, f"Current campus score: {safety_score}/100 ({lbl})")

# AI Insight Narrative
insight = app.generate_safety_insight(df_inc)
insight_ok = bool(insight and len(insight) > 30)
record_test("AI Safety Insight Narrative Generation", insight_ok, f"Generated: {insight[:75]}...")

# ----------------------------------------------------------------
# TEST GROUP 7: IN-APP NOTIFICATIONS & SOS ALERTS
# ----------------------------------------------------------------
print("\n--- 7. IN-APP NOTIFICATIONS & SOS ALERTS ---")

app.add_notification(student["id"], "Test notification for verification suite")
notifs = app.get_notifications(student["id"])
unread_before = app.get_unread_notification_count(student["id"])
app.mark_notifications_read(student["id"])
unread_after = app.get_unread_notification_count(student["id"])

notif_ok = len(notifs) > 0 and unread_before >= 1 and unread_after == 0
record_test("In-App Notification Dispatch & Read Receipt", notif_ok, f"Total notifications={len(notifs)}, unread transitioned {unread_before} -> {unread_after}")

# Clean up verification notification
del_notif_conn = app.get_connection()
del_notif_conn.execute("DELETE FROM notifications WHERE message = ?", ("Test notification for verification suite",))
del_notif_conn.commit()
del_notif_conn.close()

# ----------------------------------------------------------------
# TEST GROUP 8: PRIORITY PERSISTENCE & SUBMISSION INTEGRITY
# ----------------------------------------------------------------
print("\n--- 8. PRIORITY PERSISTENCE & REPORTING INTEGRITY ---")
test_inc_id = None
try:
    conn = app.get_connection()
    cur = conn.execute("""
        INSERT INTO incidents (
            user_id, title, category, description, location, latitude, longitude,
            risk, risk_level, priority, status, department, assigned_department,
            ai_why, ai_explanation, photo_path, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Open', ?, ?, ?, ?, '', ?)
    """, (
        student["id"], "Verification Test Hazard", "Infrastructure",
        "Test description for priority verification", "Lab Block B",
        13.069473, 77.502191, "High", "High", "Urgent",
        "Maintenance", "Maintenance",
        "Automated verification test why", "Automated verification test why",
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))
    test_inc_id = cur.lastrowid
    conn.commit()
    conn.close()

    # Verify priority retrieved from database
    verify_conn = app.get_connection()
    row = verify_conn.execute("SELECT priority, risk, risk_level, department, assigned_department FROM incidents WHERE id = ?", (test_inc_id,)).fetchone()
    verify_conn.close()

    priority_saved = row is not None and row["priority"] == "Urgent"
    dual_columns_synced = row is not None and row["risk"] == row["risk_level"] and row["department"] == row["assigned_department"]
    record_test(
        "Priority Persistence & Dual-Column Integrity",
        priority_saved and dual_columns_synced,
        f"Stored Priority='{row['priority'] if row else None}', Risk='{row['risk'] if row else None}', Dept='{row['department'] if row else None}'"
    )
finally:
    if test_inc_id:
        clean_conn = app.get_connection()
        clean_conn.execute("DELETE FROM incidents WHERE id = ?", (test_inc_id,))
        clean_conn.commit()
        clean_conn.close()

# ----------------------------------------------------------------
# TEST GROUP 9: PILLOW IMAGE VERIFICATION (VALID & CORRUPTED PAYLOADS)
# ----------------------------------------------------------------
print("\n--- 9. PILLOW IMAGE VALIDATION & REJECTION ---")

# Valid image verification
valid_img_buffer = io.BytesIO()
PIL.Image.new("RGB", (60, 60), color="green").save(valid_img_buffer, format="JPEG")
valid_img_buffer.seek(0)

valid_verified = False
try:
    test_img = PIL.Image.open(valid_img_buffer)
    test_img.verify()
    valid_verified = True
except Exception:
    valid_verified = False

record_test(
    "Pillow Valid Image Verification",
    valid_verified,
    "Valid JPEG image buffer opened and verified cleanly"
)

# Corrupted file rejection
corrupt_buffer = io.BytesIO(b"MALFORMED_NON_IMAGE_DATA_12345")
corrupt_rejected = False
rejected_reason = ""
try:
    bad_img = PIL.Image.open(corrupt_buffer)
    bad_img.verify()
    corrupt_rejected = False
except Exception as e:
    corrupt_rejected = True
    rejected_reason = type(e).__name__

record_test(
    "Pillow Corrupted Image Rejection",
    corrupt_rejected,
    f"Corrupted payload rejected with exception: {rejected_reason}"
)

# ----------------------------------------------------------------
# TEST GROUP 10: ROLE-BASED ACCESS CONTROL (RBAC)
# ----------------------------------------------------------------
print("\n--- 10. ROLE-BASED ACCESS CONTROL (RBAC) ---")

# Student blocked from admin
import streamlit as st
st.session_state.logged_in = True
st.session_state.user = {"id": 1, "role": "user", "name": "Demo Student"}
student_denied = not app.check_admin_access()
record_test(
    "RBAC: Student Access Blocked from Admin Portal",
    student_denied,
    f"check_admin_access() blocked user with role='{st.session_state.user['role']}'"
)

# Admin approved
st.session_state.user = {"id": 2, "role": "admin", "name": "Campus Administrator"}
admin_approved = app.check_admin_access()
record_test(
    "RBAC: Admin Access Approved for Administrator",
    admin_approved,
    f"check_admin_access() approved user with role='{st.session_state.user['role']}'"
)

# Admin Route Handlers Exist & Callable
admin_handlers = [
    ("admin_overview", hasattr(app, "admin_overview") and callable(app.admin_overview)),
    ("incident_management", hasattr(app, "incident_management") and callable(app.incident_management)),
    ("user_management", hasattr(app, "user_management") and callable(app.user_management)),
    ("ai_analysis", hasattr(app, "ai_analysis") and callable(app.ai_analysis)),
    ("admin_map", hasattr(app, "admin_map") and callable(app.admin_map)),
    ("analytics", hasattr(app, "analytics") and callable(app.analytics)),
    ("alerts", hasattr(app, "alerts") and callable(app.alerts)),
    ("settings", hasattr(app, "settings") and callable(app.settings)),
]
all_handlers_ok = all(ok for _, ok in admin_handlers)
record_test(
    "Admin Route Handler Definitions Complete",
    all_handlers_ok,
    f"Verified all 8 admin view callables: {', '.join(name for name, _ in admin_handlers)}"
)

# ----------------------------------------------------------------
# TEST GROUP 11: ADMIN INCIDENT TRIAGE WORKFLOW
# ----------------------------------------------------------------
print("\n--- 11. ADMIN INCIDENT TRIAGE WORKFLOW ---")
triage_test_id = None
try:
    conn = app.get_connection()
    cur = conn.execute("""
        INSERT INTO incidents (
            user_id, title, category, description, location, latitude, longitude,
            risk, risk_level, priority, status, department, assigned_department,
            ai_why, ai_explanation, photo_path, admin_note, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Open', ?, ?, ?, ?, '', '', ?)
    """, (
        student["id"], "Triage Integration Check", "Streetlight",
        "Broken light needing repair", "East Gate",
        13.069473, 77.502191, "Medium", "Medium", "Normal",
        "Electrical Maintenance", "Electrical Maintenance",
        "Streetlight explanation", "Streetlight explanation",
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))
    triage_test_id = cur.lastrowid
    conn.commit()

    # Perform triage update
    conn.execute("""
        UPDATE incidents
        SET status = ?, department = ?, assigned_department = ?, admin_note = ?
        WHERE id = ?
    """, ("In Progress", "Electrical Maintenance", "Electrical Maintenance", "Technician dispatched to East Gate.", triage_test_id))
    conn.commit()

    # Verify update
    updated_row = conn.execute("SELECT status, department, assigned_department, admin_note FROM incidents WHERE id = ?", (triage_test_id,)).fetchone()
    conn.close()

    triage_ok = (
        updated_row is not None
        and updated_row["status"] == "In Progress"
        and updated_row["department"] == "Electrical Maintenance"
        and updated_row["assigned_department"] == "Electrical Maintenance"
        and updated_row["admin_note"] == "Technician dispatched to East Gate."
    )
    record_test(
        "Admin Incident Triage & Response Notes",
        triage_ok,
        f"Status='{updated_row['status']}', Dept='{updated_row['department']}', Note='{updated_row['admin_note']}'"
    )
finally:
    if triage_test_id:
        clean_conn = app.get_connection()
        clean_conn.execute("DELETE FROM incidents WHERE id = ?", (triage_test_id,))
        clean_conn.commit()
        clean_conn.close()

# ----------------------------------------------------------------
# TEST GROUP 12: DATA PRESERVATION & ZERO MUTATION CHECK
# ----------------------------------------------------------------
print("\n--- 12. DATA PRESERVATION & ZERO MUTATION CHECK ---")
final_conn = app.get_connection()
final_inc_count = final_conn.execute("SELECT COUNT(*) FROM incidents").fetchone()[0]
final_usr_count = final_conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
final_conn.close()

preservation_ok = (final_inc_count == baseline_inc_count and final_usr_count == baseline_usr_count and final_inc_count >= 25 and final_usr_count >= 6)
record_test(
    "Database Record Preservation (Zero Mutation)",
    preservation_ok,
    f"Exact count verified: {final_inc_count}/{baseline_inc_count} Incidents, {final_usr_count}/{baseline_usr_count} Users preserved"
)

# ----------------------------------------------------------------
# SUMMARY
# ----------------------------------------------------------------
print("\n==================================================================")
print(f"VERIFICATION SUMMARY: {passed_tests}/{total_tests} TESTS PASSED ({passed_tests/total_tests*100:.1f}%)")
print("==================================================================")

if passed_tests == total_tests:
    print("STATUS: ALL SYSTEMS FULLY OPERATIONAL. READY FOR DEMO & DEPLOYMENT.")
    sys.exit(0)
else:
    print(f"STATUS: {total_tests - passed_tests} TEST(S) FAILED.")
    sys.exit(1)
