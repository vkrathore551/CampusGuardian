import os
import streamlit as st
from hotspot import show_hotspot_detection
from explainability import explain_risk
from event_logger import log_event
import pandas as pd

from database import (
    initialize_database,
    add_incident,
    get_all_incidents,
    update_incident_status,
    update_incident_department,
    update_incident_photo,
    find_duplicate
)

from dashboard import show_dashboard


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="CampusGuardian AI",
    page_icon="🛡️",
    layout="wide"
)


# ============================================================
# INITIALIZE DATABASE
# ============================================================

initialize_database()


# ============================================================
# PHOTO STORAGE
# ============================================================

PHOTO_FOLDER = "incident_photos"

os.makedirs(
    PHOTO_FOLDER,
    exist_ok=True
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>
    .main-title {
        font-size: 42px;
        font-weight: 800;
    }

    .subtitle {
        font-size: 18px;
        color: #666;
    }

    .hotspot-card {
        padding: 16px;
        border-radius: 12px;
        margin-bottom: 10px;
        border: 1px solid #ddd;
    }
    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# AI INCIDENT ANALYSIS
# ============================================================

def analyze_incident(category, description, emergency):

    text = (
        str(category) + " " +
        str(description)
    ).lower()

    departments = {
        "Fire": "Fire & Emergency Services",
        "Medical Emergency": "Medical & Health Services",
        "Water Leakage": "Maintenance Department",
        "Garbage Overflow": "Sanitation Department",
        "Pothole": "Civil & Infrastructure Department",
        "Broken Streetlight": "Electrical Department",
        "Traffic Problem": "Security & Traffic Management",
        "Unsafe Area": "Campus Security",
        "Lift/Elevator": "Maintenance Department",
        "Theft": "Campus Security",
        "Harassment": "Campus Security",
        "Other": "General Administration"
    }

    department = departments.get(
        category,
        "General Administration"
    )

    score = 30

    critical_words = [
        "fire", "smoke", "explosion", "unconscious",
        "severe", "danger", "trapped", "major accident"
    ]

    high_words = [
        "injury", "accident", "theft", "leakage",
        "flood", "broken", "unsafe", "emergency"
    ]

    medium_words = [
        "damage", "problem", "overflow",
        "pothole", "streetlight"
    ]

    if any(word in text for word in critical_words):
        score += 55
    elif any(word in text for word in high_words):
        score += 35
    elif any(word in text for word in medium_words):
        score += 20

    if emergency:
        score += 15

    score = min(score, 100)

    if category == "Fire":
        score = max(score, 90)
    elif category == "Medical Emergency":
        score = max(score, 80)
    elif category in ["Theft", "Harassment", "Unsafe Area"]:
        score = max(score, 75)
    elif category in ["Water Leakage", "Traffic Problem", "Lift/Elevator"]:
        score = max(score, 65)
    elif category in ["Garbage Overflow", "Pothole", "Broken Streetlight"]:
        score = max(score, 55)

    if score >= 85:
        risk_level = "CRITICAL"
        priority = "URGENT"
    elif score >= 70:
        risk_level = "HIGH"
        priority = "HIGH"
    elif score >= 45:
        risk_level = "MEDIUM"
        priority = "MEDIUM"
    else:
        risk_level = "LOW"
        priority = "LOW"

    why = (
        f"This incident was classified as {risk_level} risk "
        f"with a risk score of {score}/100. "
    )

    if category == "Fire":
        why += (
            "Fire and smoke can spread rapidly and may cause "
            "injuries, property damage, or evacuation requirements."
        )
    elif category == "Medical Emergency":
        why += (
            "Medical emergencies can require immediate attention "
            "to prevent serious health consequences."
        )
    elif category == "Water Leakage":
        why += (
            "Water leakage can damage campus infrastructure and "
            "may create electrical and slip hazards."
        )
    elif category == "Theft":
        why += (
            "Theft creates a security risk and requires rapid "
            "security intervention."
        )
    elif category == "Broken Streetlight":
        why += (
            "Poor lighting can increase accident and personal "
            "safety risks."
        )
    elif category == "Pothole":
        why += (
            "Road damage can create accident risks for pedestrians "
            "and vehicles."
        )
    elif category == "Garbage Overflow":
        why += (
            "Accumulated waste can create hygiene, environmental "
            "and public-health concerns."
        )
    elif category == "Lift/Elevator":
        why += (
            "Lift failures can trap people and may require "
            "immediate maintenance intervention."
        )
    elif category == "Unsafe Area":
        why += (
            "The reported location may pose a safety threat "
            "to students and staff."
        )
    else:
        why += (
            "The reported situation requires assessment by the "
            "appropriate campus department."
        )

    if emergency:
        why += " The reporter marked this incident as an emergency."

    actions = {
        "Fire": [
            "Alert campus security immediately.",
            "Contact the emergency response team.",
            "Keep students and staff away from the affected area.",
            "Evacuate the affected zone if required.",
            "Contact appropriate emergency services."
        ],
        "Medical Emergency": [
            "Contact campus medical services immediately.",
            "Provide first aid if trained personnel are available.",
            "Keep the area clear.",
            "Call external emergency medical services if required.",
            "Update the incident status after response."
        ],
        "Water Leakage": [
            "Alert the maintenance department.",
            "Restrict access to the affected area.",
            "Check for nearby electrical hazards.",
            "Stop the water source if safely possible.",
            "Repair and verify the affected infrastructure."
        ],
        "Broken Streetlight": [
            "Notify the electrical department.",
            "Mark the affected area if visibility is poor.",
            "Inspect the electrical connection.",
            "Repair or replace the streetlight.",
            "Verify that lighting is restored."
        ],
        "Pothole": [
            "Inform the civil infrastructure department.",
            "Place a temporary warning near the pothole.",
            "Inspect the road condition.",
            "Repair the damaged section.",
            "Verify road safety."
        ],
        "Garbage Overflow": [
            "Notify sanitation staff.",
            "Arrange immediate waste collection.",
            "Clean and disinfect the affected area.",
            "Check the waste collection schedule.",
            "Monitor the location."
        ],
        "Traffic Problem": [
            "Alert campus security.",
            "Control vehicle movement if necessary.",
            "Identify the source of congestion.",
            "Redirect traffic when required.",
            "Monitor the area until normal traffic resumes."
        ],
        "Theft": [
            "Alert campus security immediately.",
            "Preserve available CCTV footage.",
            "Secure the affected area.",
            "Collect relevant incident information.",
            "Escalate to authorities if required."
        ],
        "Unsafe Area": [
            "Alert campus security.",
            "Restrict access if necessary.",
            "Inspect the reported location.",
            "Identify and remove the safety hazard.",
            "Verify that the area is safe."
        ],
        "Lift/Elevator": [
            "Contact maintenance immediately.",
            "Keep people away from the lift if unsafe.",
            "Assist trapped persons using approved procedures.",
            "Contact emergency services if required.",
            "Inspect the lift before reopening it."
        ]
    }

    action_plan = actions.get(
        category,
        [
            "Notify the responsible campus department.",
            "Inspect the reported location.",
            "Take appropriate corrective action.",
            "Monitor the situation.",
            "Update the incident status."
        ]
    )

    action_text = " ".join(
        f"{i + 1}. {action}"
        for i, action in enumerate(action_plan)
    )

    return {
        "priority": priority,
        "risk_score": score,
        "risk_level": risk_level,
        "why": why,
        "action_plan": action_text,
        "department": department
    }


# ============================================================
# HOTSPOT DETECTION
# ============================================================

def build_hotspot_data(incidents):
    """
    Groups incidents by location and calculates:
    - number of incidents
    - average risk score
    - highest risk
    - emergency count
    - hotspot level
    """

    if not incidents:
        return pd.DataFrame()

    rows = []

    for incident in incidents:
        location = str(
            incident.get("location", "Unknown")
        ).strip()

        if not location:
            location = "Unknown"

        try:
            risk_score = float(
                incident.get("risk_score", 0) or 0
            )
        except (TypeError, ValueError):
            risk_score = 0

        emergency = incident.get("emergency", 0)

        try:
            emergency = int(emergency or 0)
        except (TypeError, ValueError):
            emergency = 0

        rows.append({
            "Location": location,
            "Risk Score": risk_score,
            "Emergency": emergency
        })

    df = pd.DataFrame(rows)

    if df.empty:
        return df

    hotspot = (
        df.groupby("Location", as_index=False)
        .agg(
            Incidents=("Location", "size"),
            Average_Risk=("Risk Score", "mean"),
            Highest_Risk=("Risk Score", "max"),
            Emergencies=("Emergency", "sum")
        )
    )

    hotspot["Average Risk"] = hotspot["Average_Risk"].round(1)
    hotspot["Highest Risk"] = hotspot["Highest_Risk"].round(0).astype(int)

    def get_hotspot_level(row):
        if row["Average Risk"] >= 85 or row["Highest Risk"] >= 95:
            return "CRITICAL"
        if row["Average Risk"] >= 70 or row["Highest Risk"] >= 85:
            return "HIGH"
        if row["Average Risk"] >= 45 or row["Highest Risk"] >= 65:
            return "MEDIUM"
        return "LOW"

    hotspot["Hotspot Level"] = hotspot.apply(
        get_hotspot_level,
        axis=1
    )

    hotspot = hotspot.sort_values(
        by=["Average Risk", "Incidents"],
        ascending=[False, False]
    )

    return hotspot[
        [
            "Location",
            "Incidents",
            "Average Risk",
            "Highest Risk",
            "Emergencies",
            "Hotspot Level"
        ]
    ]


def show_hotspot_detection():
    st.title("🔥 Campus Hotspot Detection")

    st.caption(
        "AI-assisted identification of campus locations "
        "with repeated or high-risk incidents."
    )

    incidents = get_all_incidents()

    if not incidents:
        st.info(
            "No incidents are available yet. "
            "Report incidents first to generate hotspot intelligence."
        )
        return

    hotspot_df = build_hotspot_data(incidents)

    if hotspot_df.empty:
        st.info("No hotspot data is available.")
        return

        # ============================================================
    # TASK 4 — AI HOTSPOT INTELLIGENCE
    # ============================================================

    st.divider()

    st.subheader("🤖 AI Hotspot Intelligence")

    # Sort locations by average risk and number of incidents
    ai_hotspot_df = hotspot_df.sort_values(
        by=["Average Risk", "Incidents"],
        ascending=[False, False]
    ).reset_index(drop=True)

    # Get the most dangerous location
    top_hotspot = ai_hotspot_df.iloc[0]

    top_location = str(top_hotspot["Location"])
    top_incidents = int(top_hotspot["Incidents"])
    top_average_risk = float(top_hotspot["Average Risk"])
    top_highest_risk = float(top_hotspot["Highest Risk"])
    top_emergencies = int(top_hotspot["Emergencies"])
    top_level = str(top_hotspot["Hotspot Level"])

    # ------------------------------------------------------------
    # AI RISK EXPLANATION
    # ------------------------------------------------------------

    if top_level == "CRITICAL":

        explanation = (
            f"🔴 **Critical hotspot detected at {top_location}.**\n\n"
            f"This location has **{top_incidents} incident(s)** with "
            f"an average risk score of **{top_average_risk:.0f}/100**. "
            f"The highest recorded risk is **{top_highest_risk:.0f}/100**. "
            f"There are **{top_emergencies} emergency incident(s)** "
            f"associated with this location.\n\n"
            f"🚨 **AI Recommendation:** Immediate safety attention "
            f"and increased monitoring are recommended."
        )

        st.error(explanation)

    elif top_level == "HIGH":

        explanation = (
            f"🟠 **High-risk hotspot detected at {top_location}.**\n\n"
            f"This location has **{top_incidents} incident(s)** with "
            f"an average risk score of **{top_average_risk:.0f}/100**. "
            f"The highest recorded risk is **{top_highest_risk:.0f}/100**. "
            f"There are **{top_emergencies} emergency incident(s)** "
            f"associated with this location.\n\n"
            f"⚠️ **AI Recommendation:** Increase monitoring and "
            f"prioritize unresolved incidents in this area."
        )

        st.warning(explanation)

    elif top_level == "MEDIUM":

        explanation = (
            f"🟡 **Moderate hotspot detected at {top_location}.**\n\n"
            f"This location has **{top_incidents} incident(s)** with "
            f"an average risk score of **{top_average_risk:.0f}/100**. "
            f"The highest recorded risk is **{top_highest_risk:.0f}/100**. "
            f"There are **{top_emergencies} emergency incident(s)** "
            f"associated with this location.\n\n"
            f"💡 **AI Recommendation:** Continue monitoring this "
            f"location and investigate repeated incidents."
        )

        st.info(explanation)

    else:

        explanation = (
            f"🟢 **Low-risk hotspot detected at {top_location}.**\n\n"
            f"This location has **{top_incidents} incident(s)** with "
            f"an average risk score of **{top_average_risk:.0f}/100**.\n\n"
            f"💡 **AI Recommendation:** Current risk levels appear "
            f"manageable. Continue routine monitoring."
        )

        st.success(explanation)

    # ------------------------------------------------------------
    # HOTSPOT RANKING
    # ------------------------------------------------------------

    st.subheader("🏆 AI Hotspot Ranking")

    ranking_df = ai_hotspot_df[
        [
            "Location",
            "Incidents",
            "Average Risk",
            "Highest Risk",
            "Emergencies",
            "Hotspot Level"
        ]
    ].copy()

    st.dataframe(
    ranking_df,
    width="stretch",
    hide_index=True
)
    

    critical_count = int(
        (hotspot_df["Hotspot Level"] == "CRITICAL").sum()
    )
    high_count = int(
        (hotspot_df["Hotspot Level"] == "HIGH").sum()
    )
    total_locations = len(hotspot_df)

    top_hotspot = hotspot_df.iloc[0]

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "📍 Locations",
        total_locations
    )

    c2.metric(
        "🔴 Critical Hotspots",
        critical_count
    )

    c3.metric(
        "🟠 High-Risk Hotspots",
        high_count
    )

    c4.metric(
        "🔥 Top Hotspot",
        str(top_hotspot["Location"])[:20]
    )

    st.divider()

    st.subheader("🔥 Highest-Risk Campus Locations")

    display_df = hotspot_df.copy()

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    st.subheader("📊 Incident Concentration")

    chart_df = hotspot_df[
        ["Location", "Incidents"]
    ].set_index("Location")

    st.bar_chart(chart_df)

    # ============================================================
# ============================================================
# AI HOTSPOT SUMMARY
# ============================================================

st.divider()

st.subheader("🤖 AI Hotspot Summary")

# Load incidents from database
incidents = get_all_incidents()

# Find the most critical hotspot
hotspot_df = build_hotspot_data(incidents)
top_hotspot = hotspot_df.iloc[0]

top_location = str(top_hotspot["Location"])
top_incidents = int(top_hotspot["Incidents"])
top_risk = float(top_hotspot["Average Risk"])
top_level = str(top_hotspot["Hotspot Level"])
top_emergencies = int(top_hotspot["Emergencies"])

# Generate AI-style explanation
if top_level == "CRITICAL":
    summary = (
        f"🚨 **Critical hotspot detected at {top_location}.** "
        f"This location has **{top_incidents} incident(s)** with an "
        f"average risk score of **{top_risk:.0f}/100**. "
        f"There are **{top_emergencies} emergency incident(s)**. "
        f"Immediate safety attention is recommended."
    )

elif top_level == "HIGH":
    summary = (
        f"⚠️ **High-risk hotspot detected at {top_location}.** "
        f"This location has **{top_incidents} incident(s)** with an "
        f"average risk score of **{top_risk:.0f}/100**. "
        f"Campus authorities should review this location and monitor "
        f"new incidents closely."
    )

elif top_level == "MEDIUM":
    summary = (
        f"🟠 **Moderate hotspot detected at {top_location}.** "
        f"This location has **{top_incidents} incident(s)** with an "
        f"average risk score of **{top_risk:.0f}/100**. "
        f"Continued monitoring is recommended."
    )

else:
    summary = (
        f"🟢 **Low-risk hotspot detected at {top_location}.** "
        f"This location has **{top_incidents} incident(s)**. "
        f"Current risk levels appear manageable."
    )
    st.info(summary)

    st.divider()

    st.subheader("🚨 Hotspot Intelligence")

    for _, row in hotspot_df.head(5).iterrows():
        level = row["Hotspot Level"]
        location = row["Location"]

        message = (
            f"**{location}** has "
            f"**{int(row['Incidents'])} incident(s)**, "
            f"an average risk of **{row['Average Risk']:.0f}/100**, "
            f"and **{int(row['Emergencies'])} emergency incident(s)**."
        )

        if level == "CRITICAL":
            st.error(
                f"🔴 **CRITICAL HOTSPOT - {location}**\n\n{message}"
            )

        elif level == "HIGH":
            st.warning(
                f"🟠 **HIGH-RISK HOTSPOT - {location}**\n\n{message}"
            )

        elif level == "MEDIUM":
            st.info(
                f"🟡 **MEDIUM-RISK HOTSPOT - {location}**\n\n{message}"
            )

        else:
            st.success(
                f"🟢 **LOW-RISK HOTSPOT - {location}**\n\n{message}"
            )

        message = (
            f"**{location}** has "
            f"**{int(row['Incidents'])} incident(s)**, "
            f"an average risk of **{row['Average Risk']}/100**, "
            f"and **{int(row['Emergencies'])} emergency incident(s)**."
        )

        if level == "CRITICAL":
            st.error(
                f"🔴 **CRITICAL HOTSPOT — {location}**\n\n"
                + message
            )
        elif level == "HIGH":
            st.warning(
                f"🟠 **HIGH-RISK HOTSPOT — {location}**\n\n"
                + message
            )
        elif level == "MEDIUM":
            st.info(
                f"🟡 **MEDIUM-RISK AREA — {location}**\n\n"
                + message
            )
        else:
            st.success(
                f"🟢 **LOW-RISK AREA — {location}**\n\n"
                + message
            )

    st.divider()

    st.subheader("🗺️ Coordinate-Based Campus Risk Map")

    map_rows = []

    for incident in incidents:
        try:
            lat = float(incident.get("latitude"))
            lon = float(incident.get("longitude"))

            if -90 <= lat <= 90 and -180 <= lon <= 180:
                map_rows.append({
                    "lat": lat,
                    "lon": lon
                })
        except (TypeError, ValueError):
            continue

    if map_rows:
        map_df = pd.DataFrame(map_rows)
        st.map(map_df)
        st.caption(
            "The map uses the latitude and longitude recorded "
            "with each incident."
        )
    else:
        st.info(
            "No valid latitude/longitude data is available "
            "for the incident map."
        )


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title(
    "🛡️ CampusGuardian AI"
)

st.sidebar.write(
    "AI-powered campus safety and incident management system."
)

st.sidebar.markdown(
    "### Navigation"
)

page = st.sidebar.radio(
    "",
    [
        "🚨 Report Incident",
        "📋 Incident Management",
        "📊 Dashboard",
        "🔥 Hotspot Detection"
    ],
    key="main_navigation"
)


# ============================================================
# REPORT INCIDENT
# ============================================================

if page == "🚨 Report Incident":

    st.markdown(
        '<div class="main-title">'
        '🛡️ CampusGuardian AI'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitle">'
        'Smart Campus Safety & Emergency Intelligence Platform'
        '</div>',
        unsafe_allow_html=True
    )

    st.divider()

    st.header("🚨 Report a Campus Incident")

    col1, col2 = st.columns(2)

    categories = [
        "Fire",
        "Medical Emergency",
        "Water Leakage",
        "Garbage Overflow",
        "Pothole",
        "Broken Streetlight",
        "Traffic Problem",
        "Unsafe Area",
        "Lift/Elevator",
        "Theft",
        "Harassment",
        "Other"
    ]

    with col1:

        category = st.selectbox(
            "Incident Category",
            categories,
            key="incident_category"
        )

        location = st.text_input(
            "📍 Location",
            placeholder="Example: Main Building, Ground Floor"
        )

        latitude = st.number_input(
    "🌐 Latitude",
    value=13.0676204,
    format="%.6f"
)

        longitude = st.number_input(
    "🌐 Longitude",
    value=77.5019042,
    format="%.6f"
)

    with col2:

        description = st.text_area(
            "📝 Describe the Problem",
            placeholder="Example: Major water leakage near the corridor...",
            height=150
        )

        emergency = st.checkbox(
            "🚨 This is an emergency"
        )

    st.subheader("📷 Incident Evidence")

    uploaded_file = st.file_uploader(
        "Upload Incident Photo",
        type=["jpg", "jpeg", "png", "webp"],
        help=(
            "Upload a photo showing the incident. "
            "The image will be saved with the incident."
        ),
        key="incident_photo"
    )

    if uploaded_file is not None:

        st.image(
            uploaded_file,
            caption="Uploaded incident evidence",
            use_container_width=True
        )

    st.divider()

    if st.button(
        "🤖 ANALYZE INCIDENT",
        use_container_width=True,
        key="analyze_incident_button"
    ):

        if not location.strip():

            st.error("Please enter the incident location.")

        elif not description.strip():

            st.error("Please describe the problem.")

        else:

            result = analyze_incident(
                category,
                description,
                emergency
            )

            st.session_state["analysis_result"] = result

    if "analysis_result" in st.session_state:

        result = st.session_state["analysis_result"]

        st.subheader("🤖 AI Incident Analysis")

        c1, c2, c3, c4 = st.columns(4)

        c1.metric(
            "Risk Score",
            f"{result['risk_score']}/100"
        )

        c2.metric(
            "Risk Level",
            result["risk_level"]
        )

        c3.metric(
            "Priority",
            result["priority"]
        )

        c4.metric(
            "Department",
            result["department"]
        )

        st.info(
            "💡 WHY: " +
            result["why"]
        )

        st.warning(
            "🚨 Recommended Action\n\n" +
            result["action_plan"]
        )

        duplicate = find_duplicate(
            category,
            location,
            description
        )

        if duplicate:

            st.warning(
                f"⚠️ A similar incident already exists "
                f"(Incident #{duplicate['id']}). "
                f"You can still save this report if "
                f"it is a new occurrence."
            )

        else:

            st.success(
                "✅ No similar incident detected."
            )

        st.divider()

        if st.button(
            "💾 SAVE INCIDENT",
            use_container_width=True,
            key="save_incident_button"
        ):

            duplicate_id = (
                duplicate["id"]
                if duplicate
                else None
            )

            photo_path = None

            try:

                if uploaded_file is not None:

                    safe_extension = os.path.splitext(
                        uploaded_file.name
                    )[1].lower()

                    if safe_extension not in [
                        ".jpg",
                        ".jpeg",
                        ".png",
                        ".webp"
                    ]:
                        safe_extension = ".jpg"

                    photo_filename = (
                        f"incident_"
                        f"{category.lower().replace(' ', '_')}_"
                        f"{int(__import__('time').time())}"
                        f"{safe_extension}"
                    )

                    photo_path = os.path.join(
                        PHOTO_FOLDER,
                        photo_filename
                    )

                    with open(
                        photo_path,
                        "wb"
                    ) as photo_file:

                        photo_file.write(
                            uploaded_file.getbuffer()
                        )

                incident_id = add_incident(

                    title=f"{category} Incident",

                    description=description,

                    category=category,

                    location=location,

                    latitude=latitude,

                    longitude=longitude,

                    priority=result["priority"],

                    risk_score=result["risk_score"],

                    risk_level=result["risk_level"],

                    ai_explanation=result["why"],

                    recommended_action=result["action_plan"],

                    assigned_department=result["department"],

                    status="OPEN",

                    duplicate_of=duplicate_id,

                    emergency=1 if emergency else 0,

                    photo_path=photo_path
                )

                if photo_path:

                    update_incident_photo(
                        incident_id,
                        photo_path
                    )

                st.success(
                    f"✅ Incident #{incident_id} saved successfully!"
                )

                if photo_path:

                    st.success(
                        "📷 Incident photo saved successfully."
                    )

                st.info(
                    "Go to 📋 Incident Management to view the incident."
                )

                if "analysis_result" in st.session_state:

                    del st.session_state["analysis_result"]

            except Exception as e:

                if (
                    photo_path
                    and os.path.exists(photo_path)
                ):

                    try:
                        os.remove(photo_path)
                    except Exception:
                        pass

                st.error(
                    "❌ Failed to save incident."
                )

                st.exception(e)


# ============================================================
# INCIDENT MANAGEMENT
# ============================================================

elif page == "📋 Incident Management":

    st.title("📋 Incident Management")

    incidents = get_all_incidents()

    if not incidents:

        st.info(
            "No incidents have been reported yet."
        )

    else:

        st.write(
            f"Total incidents: **{len(incidents)}**"
        )

        st.divider()

        for incident in incidents:

            incident_id = incident["id"]

            risk = incident.get(
                "risk_level",
                "MEDIUM"
            )

            category = incident.get(
                "category",
                "Incident"
            )

            title = (
                f"#{incident_id} — "
                f"{category} — "
                f"{risk}"
            )

            with st.expander(title):

                col1, col2 = st.columns(2)

                with col1:

                    st.write("**Description:**")
                    st.write(
                        incident.get(
                            "description",
                            ""
                        )
                    )

                    st.write("**Location:**")
                    st.write(
                        incident.get(
                            "location",
                            ""
                        )
                    )

                    st.write("**Risk Score:**")
                    st.write(
                        f"{incident.get('risk_score', 0)}/100"
                    )

                    st.write("**Risk Level:**")
                    st.write(
                        incident.get(
                            "risk_level",
                            ""
                        )
                    )

                    st.write("**Priority:**")
                    st.write(
                        incident.get(
                            "priority",
                            ""
                        )
                    )

                with col2:

                    st.write("**Department:**")
                    st.write(
                        incident.get(
                            "assigned_department",
                            "Not Assigned"
                        )
                    )

                    st.write("**Current Status:**")
                    st.write(
                        incident.get(
                            "status",
                            "OPEN"
                        )
                    )

                    st.write("**Created:**")
                    st.write(
                        incident.get(
                            "created_at",
                            ""
                        )
                    )

                    if incident.get("emergency"):

                        st.error(
                            "🚨 EMERGENCY INCIDENT"
                        )

                st.info(
                    "💡 WHY: " +
                    str(
                        incident.get(
                            "ai_explanation",
                            ""
                        )
                    )
                )

                st.warning(
                    "🚨 ACTION: " +
                    str(
                        incident.get(
                            "recommended_action",
                            ""
                        )
                    )
                )

                photo_path = incident.get(
                    "photo_path"
                )

                if (
                    photo_path
                    and os.path.exists(photo_path)
                ):

                    st.subheader(
                        "📷 Incident Evidence"
                    )

                    st.image(
                        photo_path,
                        caption=(
                            f"Evidence for "
                            f"Incident #{incident_id}"
                        ),
                        use_container_width=True
                    )

                else:

                    st.caption(
                        "📷 No incident photo uploaded."
                    )

                st.divider()

                status_options = [
                    "OPEN",
                    "ASSIGNED",
                    "IN PROGRESS",
                    "RESOLVED"
                ]

                current_status = incident.get(
                    "status",
                    "OPEN"
                )

                if current_status not in status_options:
                    current_status = "OPEN"

                new_status = st.selectbox(
                    "Update Status",
                    status_options,
                    index=status_options.index(
                        current_status
                    ),
                    key=f"status_{incident_id}"
                )

                department_options = [
                    "Fire & Emergency Services",
                    "Medical & Health Services",
                    "Maintenance Department",
                    "Sanitation Department",
                    "Civil & Infrastructure Department",
                    "Electrical Department",
                    "Security & Traffic Management",
                    "Campus Security",
                    "General Administration"
                ]

                current_department = incident.get(
                    "assigned_department",
                    "General Administration"
                )

                if (
                    current_department
                    not in department_options
                ):
                    current_department = (
                        "General Administration"
                    )

                new_department = st.selectbox(
                    "Assigned Department",
                    department_options,
                    index=department_options.index(
                        current_department
                    ),
                    key=f"department_{incident_id}"
                )

                if st.button(
                    "💾 UPDATE INCIDENT",
                    key=f"update_{incident_id}"
                ):

                    try:

                        update_incident_status(
                            incident_id,
                            new_status
                        )

                        update_incident_department(
                            incident_id,
                            new_department
                        )

                        st.success(
                            "✅ Incident updated successfully."
                        )

                        st.rerun()

                    except Exception as e:

                        st.error(
                            "❌ Failed to update incident."
                        )

                        st.exception(e)


# ============================================================
# DASHBOARD
# ============================================================

elif page == "📊 Dashboard":

    # Dashboard code remains inside dashboard.py.
    # This keeps dashboard variables separate from Report Incident.

    show_dashboard()


# ============================================================
# HOTSPOT DETECTION
# ============================================================

elif page == "🔥 Hotspot Detection":

    show_hotspot_detection()
# ============================================================
# TASK 12 — EXPLAINABLE AI + EVENT LOGGING
# ============================================================

st.divider()

st.subheader("🧠 Explainable AI & Event Logging")

st.caption(
    "Understand why the AI assigned a particular risk level "
    "and keep a record of important safety events."
)

# ------------------------------------------------------------
# SELECT INCIDENT
# ------------------------------------------------------------

if incidents:

    incident_options = []

    for incident in incidents:

        incident_id = incident.get("id", "Unknown")
        title = incident.get("title", "Incident")
        location = incident.get("location", "Unknown")

        incident_options.append(
            f"{incident_id} — {title} — {location}"
        )

    selected_incident = st.selectbox(
        "Select an incident to explain",
        incident_options
    )

    selected_index = incident_options.index(
        selected_incident
    )

    selected = incidents[selected_index]

    # --------------------------------------------------------
    # INCIDENT INFORMATION
    # --------------------------------------------------------

    incident_id = selected.get("id", "Unknown")

    title = selected.get(
        "title",
        "Unknown Incident"
    )

    category = selected.get(
        "category",
        "Unknown"
    )

    location = selected.get(
        "location",
        "Unknown"
    )

    risk_level = selected.get(
        "risk_level",
        "UNKNOWN"
    )

    risk_score = selected.get(
        "risk_score",
        0
    )

    # --------------------------------------------------------
    # EMERGENCY CHECK
    # --------------------------------------------------------

    emergency_value = selected.get(
        "is_emergency",
        selected.get("emergency", False)
    )

    emergency = str(
        emergency_value
    ).lower() in [
        "true",
        "1",
        "yes",
        "y",
        "emergency"
    ]

    # --------------------------------------------------------
    # GENERATE EXPLANATION
    # --------------------------------------------------------

    explanation = explain_risk(
        risk_score=risk_score,
        risk_level=risk_level,
        category=category,
        emergency=emergency,
        location=location
    )

    st.markdown("### 🔍 Why did the AI assign this risk?")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Risk Score",
            f"{float(risk_score):.0f}/100"
        )

    with col2:
        st.metric(
            "Risk Level",
            str(risk_level).upper()
        )

    with col3:
        st.metric(
            "Emergency",
            "YES" if emergency else "NO"
        )

    st.info(
        f"🧠 **AI Explanation:** {explanation}"
    )

    # --------------------------------------------------------
    # LOG EVENT
    # --------------------------------------------------------

    if st.button(
        "📝 Log AI Safety Event",
        key="log_ai_event"
    ):

        log_event(
            event_type="AI_RISK_ANALYSIS",
            incident_id=incident_id,
            location=location,
            risk_level=risk_level,
            risk_score=risk_score,
            reason=explanation
        )

        st.success(
            "✅ AI safety event successfully logged."
        )

else:

    st.info(
        "No incidents available for Explainable AI analysis."
    )