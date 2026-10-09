# 🛡️ CampusGuardian AI
> **Intelligent Campus Safety & Rapid Incident Response Platform**  
> *Developed for Sapthagiri NPS University — Hackathon Demonstration & Production Deployment*

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.65.0-FF4B4B.svg)](https://streamlit.io)
[![Database](https://img.shields.io/badge/SQLite-Database-003B57.svg)](https://sqlite.org)
[![Security](https://img.shields.io/badge/Auth-PBKDF2--HMAC--SHA256-green.svg)](https://docs.python.org/3/library/hashlib.html)
[![Tests](https://img.shields.io/badge/Verification%20Suite-26%2F26%20Passing-brightgreen.svg)](test_complete_verification.py)

---

## 📌 Overview

**CampusGuardian AI** is an end-to-end smart campus safety operations system. It bridges the gap between students reporting hazardous events and administrative response teams dispatching assistance.

By pairing automated heuristic **AI Risk Analysis** with **Geospatial Hotspot Detection**, **Evidence Photo Media Handling**, and an **Emergency SOS Dispatch Center**, CampusGuardian ensures life-safety risks (such as fires, elevator traps, violence, and electrical hazards) are immediately triaged and resolved.

---

## 🚀 Key Features

### 1. 🎓 Student Safety Workspace
* **Incident Reporting with Perceived Priority:** Easy reporting interface capturing hazard title, category, perceived priority (`Urgent`, `High`, `Normal`, `Low`), detailed narrative, and specific campus location.
* **Campus GPS Integration:** Auto-attaches Sapthagiri NPS University reference coordinates (13.069473, 77.502191) or accepts custom coordinates.
* **Pillow-Verified Evidence Photo Upload:** File upload supporting JPEG, PNG, and WebP formats. Uploaded image bytes are verified with Pillow (`Image.verify()`) before saving to disk to safely reject corrupted or malformed files.
* **Loading & Submission Feedback:** Real-time processing indicators with instant feedback summarizing assessed risk, assigned team, and photo preview.
* **Interactive Live Status Tracker:** Real-time visual progress pipeline showing each report transitioning through:
  $$\text{Reported} \longrightarrow \text{Assigned} \longrightarrow \text{In Progress} \longrightarrow \text{Resolved}$$
* **My Reports Tracking:** Dedicated student archive displaying report priority badges, current status, AI explanation, admin response notes, and evidence photo downloads.
* **Direct Emergency SOS:** One-touch panic button that dispatches critical alerts to campus security with automated high-priority triage and urgent helpline reference numbers (112, 101, 102, Campus Control Room).

### 2. 🏛️ Administrator Command Center
* **Strict Role-Based Access Control (RBAC):** Dedicated administrator portal protected by server-side `check_admin_access()` guards that block non-admin accounts from accessing administrative functions or URLs.
* **Campus Operational Safety Score (0–100):** Real-time composite health metric incorporating risk volume, critical hazard density, and 7-day velocity.
* **Interactive Analytics & Heatmaps:** Plotly risk distribution bar charts, status donut charts, volume timelines, and OpenStreetMap risk heatmaps.
* **Incident Triage & Response Center:**
  * Multi-faceted filtering by Risk (`Critical`, `High`, `Medium`, `Low`), Status (`Open`, `Assigned`, `In Progress`, `Resolved`), Category, Priority (`Urgent`, `High`, `Normal`, `Low`), or Full-Text search query.
  * Evidence Photo viewer with high-resolution download option and graceful missing-file fallback handling.
  * Status updater (`Open` ➔ `Assigned` ➔ `In Progress` ➔ `Resolved`).
  * Team routing (`Campus Security`, `Maintenance`, `Medical Unit`, `Fire & Safety`, `Electrical Maintenance`, etc.).
  * Response notes logged directly to the student's in-app notification feed.
* **User Management:** Review registered accounts and administrator access levels without exposing password hashes.

### 3. 🤖 Explainable AI Risk Intelligence
* **Rule-based Heuristic Engine:** Instant categorization into `Critical`, `High`, `Medium`, and `Low` risk levels.
* **Transparent Justification:** Clear explanations of why an incident was classified with a given severity.
* **Automated Department Routing:** Suggests the correct campus unit responsible for remediation.

### 4. 🔒 Data & Security Architecture
* **Salted PBKDF2 Password Hashing:** 120,000 iterations using `hashlib.pbkdf2_hmac` with cryptographically secure salts (`secrets.token_hex`).
* **Backward-Compatible Auto-Upgrade:** Seamlessly validates legacy hashes and upgrades them to salted PBKDF2 on login.
* **SQL Injection Protection:** Fully parameterized SQLite queries (`?`) across all endpoints.
* **Dual-Schema Harmonization:** Synchronized column persistence supporting both `risk`/`risk_level`, `department`/`assigned_department`, `ai_why`/`ai_explanation`, and `priority`.
* **Zero Credential Exposure:** No API keys, secret tokens, or hardcoded passwords stored in the repository.

---

## 🔑 Hackathon Demo Credentials

Use these pre-configured demo accounts during testing and evaluation:

| Role | Email | Password | Access Level |
| :--- | :--- | :--- | :--- |
| **Demo Student** | `student@campusguardian.com` | `student123` | Student Dashboard, Report Incident, Status Tracker, SOS, My Reports |
| **Campus Admin** | `admin@campusguardian.com` | `admin123` | Safety Command Center, Incident Triage, Status Updater, Analytics |

*(New student accounts can also be created via the "Create Account" tab on the sign-in screen.)*

---

## 💻 Tech Stack

* **Frontend & Web Server:** Streamlit 1.65.0
* **Data Processing & Analytics:** Pandas, NumPy
* **Visualizations & Heatmaps:** Plotly Express & Plotly Graph Objects
* **Image Processing:** Pillow (PIL), OpenCV (`opencv-python`)
* **Security & Crypto:** Hashlib, Secrets
* **Database:** SQLite 3 (`campusguardian.db`)

---

## 🛠️ Quickstart (Local Run)

### 1. Clone & Navigate to Repository
```bash
git clone https://github.com/vkrathore551/CampusGuardian.git
cd CampusGuardian
```

### 2. Set Up Virtual Environment
```bash
# Windows
python -m venv .venv
.\.venv\Scripts\activate

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Automated Verification Suite
Verify database schema integrity, dependencies, authentication, photo resolution, and RBAC security:
```bash
python test_complete_verification.py
```
*(All 26 automated integration tests should report `[✅ PASS]`.)*

### 5. Launch the Application
```bash
streamlit run app.py
```
Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## 🗄️ Database Architecture

* **Database Engine:** SQLite 3
* **Primary Database File:** `campusguardian.db`
* **Tables:**
  * `users` — User credentials, role (`user` or `admin`), department, contact details, creation timestamp.
  * `incidents` — Incident records, category, priority, risk score, risk level, description, location, coordinates, photo path, status, assigned department, admin response note, timestamps.
  * `notifications` — In-app alerts, read receipts, timestamps.
* **Storage Path for Media:** `incident_photos/` (cross-platform path resolution handles forward and backward slashes gracefully).

---

## 🌐 Production Deployment Guide

### Option A: Streamlit Community Cloud (Recommended for Hackathons)
1. Push the repository to GitHub.
2. Sign in to [share.streamlit.io](https://share.streamlit.io/).
3. Click **"New app"**, select the repository (`CampusGuardian`), branch (`main`), and set **Main file path** to `app.py`.
4. Click **Deploy**. The app will build and deploy automatically.

### Option B: Docker Container
Build and run the containerized application:
```bash
docker build -t campusguardian .
docker run -p 8501:8501 campusguardian
```

---

## 📄 License & Attribution
Developed for the **Sapthagiri NPS University** Hackathon. All rights reserved.
