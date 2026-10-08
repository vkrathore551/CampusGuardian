import os
import streamlit as st

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

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# AI INCIDENT ANALYSIS
# ============================================================

def analyze_incident(
    category,
    description,
    emergency
):

    text = (
        str(category) + " " +
        str(description)
    ).lower()


    # --------------------------------------------------------
    # DEPARTMENT ASSIGNMENT
    # --------------------------------------------------------

    departments = {

        "Fire":
            "Fire & Emergency Services",

        "Medical Emergency":
            "Medical & Health Services",

        "Water Leakage":
            "Maintenance Department",

        "Garbage Overflow":
            "Sanitation Department",

        "Pothole":
            "Civil & Infrastructure Department",

        "Broken Streetlight":
            "Electrical Department",

        "Traffic Problem":
            "Security & Traffic Management",

        "Unsafe Area":
            "Campus Security",

        "Lift/Elevator":
            "Maintenance Department",

        "Theft":
            "Campus Security",

        "Harassment":
            "Campus Security",

        "Other":
            "General Administration"
    }

    department = departments.get(
        category,
        "General Administration"
    )


    # --------------------------------------------------------
    # BASE RISK SCORE
    # --------------------------------------------------------

    score = 30


    critical_words = [
        "fire",
        "smoke",
        "explosion",
        "unconscious",
        "severe",
        "danger",
        "trapped",
        "major accident"
    ]


    high_words = [
        "injury",
        "accident",
        "theft",
        "leakage",
        "flood",
        "broken",
        "unsafe",
        "emergency"
    ]


    medium_words = [
        "damage",
        "problem",
        "overflow",
        "pothole",
        "streetlight"
    ]


    if any(
        word in text
        for word in critical_words
    ):

        score += 55

    elif any(
        word in text
        for word in high_words
    ):

        score += 35

    elif any(
        word in text
        for word in medium_words
    ):

        score += 20


    # Emergency increases risk

    if emergency:
        score += 15


    score = min(
        score,
        100
    )


    # --------------------------------------------------------
    # CATEGORY BASED RISK
    # --------------------------------------------------------

    if category == "Fire":

        score = max(
            score,
            90
        )

    elif category == "Medical Emergency":

        score = max(
            score,
            80
        )

    elif category in [
        "Theft",
        "Harassment",
        "Unsafe Area"
    ]:

        score = max(
            score,
            75
        )

    elif category in [
        "Water Leakage",
        "Traffic Problem",
        "Lift/Elevator"
    ]:

        score = max(
            score,
            65
        )

    elif category in [
        "Garbage Overflow",
        "Pothole",
        "Broken Streetlight"
    ]:

        score = max(
            score,
            55
        )


    # --------------------------------------------------------
    # RISK LEVEL
    # --------------------------------------------------------

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


    # --------------------------------------------------------
    # AI WHY EXPLANATION
    # --------------------------------------------------------

    why = (
        f"This incident was classified as "
        f"{risk_level} risk with a risk score "
        f"of {score}/100. "
    )


    if category == "Fire":

        why += (
            "Fire and smoke can spread rapidly "
            "and may cause injuries, property damage, "
            "or evacuation requirements."
        )

    elif category == "Medical Emergency":

        why += (
            "Medical emergencies can require "
            "immediate attention to prevent "
            "serious health consequences."
        )

    elif category == "Water Leakage":

        why += (
            "Water leakage can damage campus "
            "infrastructure and may create "
            "electrical and slip hazards."
        )

    elif category == "Theft":

        why += (
            "Theft creates a security risk "
            "and requires rapid security intervention."
        )

    elif category == "Broken Streetlight":

        why += (
            "Poor lighting can increase accident "
            "and personal safety risks."
        )

    elif category == "Pothole":

        why += (
            "Road damage can create accident "
            "risks for pedestrians and vehicles."
        )

    elif category == "Garbage Overflow":

        why += (
            "Accumulated waste can create hygiene, "
            "environmental and public-health concerns."
        )

    elif category == "Lift/Elevator":

        why += (
            "Lift failures can trap people and "
            "may require immediate maintenance intervention."
        )

    elif category == "Unsafe Area":

        why += (
            "The reported location may pose "
            "a safety threat to students and staff."
        )

    else:

        why += (
            "The reported situation requires assessment "
            "by the appropriate campus department."
        )


    if emergency:

        why += (
            " The reporter marked this incident "
            "as an emergency."
        )


    # --------------------------------------------------------
    # RECOMMENDED ACTION PLAN
    # --------------------------------------------------------

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
# SIDEBAR
# ============================================================

st.sidebar.title(
    "🛡️ CampusGuardian AI"
)

st.sidebar.write(
    "AI-powered campus safety and "
    "incident management system."
)

st.sidebar.markdown(
    "### Navigation"
)


page = st.sidebar.radio(
    "",
    [
        "🚨 Report Incident",
        "📋 Incident Management",
        "📊 Dashboard"
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

    st.header(
        "🚨 Report a Campus Incident"
    )


    # --------------------------------------------------------
    # INPUTS
    # --------------------------------------------------------

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
            value=12.971600,
            format="%.6f"
        )


        longitude = st.number_input(
            "🌐 Longitude",
            value=77.594600,
            format="%.6f"
        )


    with col2:

        description = st.text_area(
            "📝 Describe the Problem",
            placeholder=(
                "Example: Major water leakage "
                "near the corridor..."
            ),
            height=150
        )


        emergency = st.checkbox(
            "🚨 This is an emergency"
        )


    # --------------------------------------------------------
    # PHOTO UPLOAD
    # --------------------------------------------------------

    st.subheader(
        "📷 Incident Evidence"
    )


    uploaded_file = st.file_uploader(
        "Upload Incident Photo",
        type=[
            "jpg",
            "jpeg",
            "png",
            "webp"
        ],
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


    # --------------------------------------------------------
    # ANALYZE BUTTON
    # --------------------------------------------------------

    if st.button(
        "🤖 ANALYZE INCIDENT",
        use_container_width=True,
        key="analyze_incident_button"
    ):

        if not location.strip():

            st.error(
                "Please enter the incident location."
            )

        elif not description.strip():

            st.error(
                "Please describe the problem."
            )

        else:

            result = analyze_incident(
                category,
                description,
                emergency
            )

            st.session_state[
                "analysis_result"
            ] = result


    # --------------------------------------------------------
    # SHOW ANALYSIS
    # --------------------------------------------------------

    if "analysis_result" in st.session_state:

        result = st.session_state[
            "analysis_result"
        ]


        st.subheader(
            "🤖 AI Incident Analysis"
        )


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


        # ----------------------------------------------------
        # DUPLICATE CHECK
        # ----------------------------------------------------

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


        # ----------------------------------------------------
        # SAVE INCIDENT
        # ----------------------------------------------------

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

                # --------------------------------------------
                # SAVE PHOTO FIRST
                # --------------------------------------------

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


                # --------------------------------------------
                # SAVE INCIDENT
                # --------------------------------------------

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


                # --------------------------------------------
                # EXTRA PHOTO UPDATE
                # --------------------------------------------

                # This is kept as a safety step.
                # If a photo exists, ensure the database
                # contains its path.

                if photo_path:

                    update_incident_photo(
                        incident_id,
                        photo_path
                    )


                # --------------------------------------------
                # SUCCESS
                # --------------------------------------------

                st.success(
                    f"✅ Incident #{incident_id} "
                    f"saved successfully!"
                )


                if photo_path:

                    st.success(
                        "📷 Incident photo saved successfully."
                    )


                st.info(
                    "Go to 📋 Incident Management "
                    "to view the incident."
                )


                # Clear analysis

                if "analysis_result" in st.session_state:

                    del st.session_state[
                        "analysis_result"
                    ]


            except Exception as e:

                # If photo was saved but database failed,
                # remove the unused photo.

                if (
                    photo_path
                    and os.path.exists(photo_path)
                ):

                    try:

                        os.remove(
                            photo_path
                        )

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

    st.title(
        "📋 Incident Management"
    )


    incidents = get_all_incidents()


    if not incidents:

        st.info(
            "No incidents have been reported yet."
        )


    else:

        st.write(
            f"Total incidents: "
            f"**{len(incidents)}**"
        )


        st.divider()


        # ----------------------------------------------------
        # INCIDENT LIST
        # ----------------------------------------------------

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


                # --------------------------------------------
                # LEFT SIDE
                # --------------------------------------------

                with col1:

                    st.write(
                        "**Description:**"
                    )

                    st.write(
                        incident.get(
                            "description",
                            ""
                        )
                    )


                    st.write(
                        "**Location:**"
                    )

                    st.write(
                        incident.get(
                            "location",
                            ""
                        )
                    )


                    st.write(
                        "**Risk Score:**"
                    )

                    st.write(
                        f"{incident.get('risk_score', 0)}/100"
                    )


                    st.write(
                        "**Risk Level:**"
                    )

                    st.write(
                        incident.get(
                            "risk_level",
                            ""
                        )
                    )


                    st.write(
                        "**Priority:**"
                    )

                    st.write(
                        incident.get(
                            "priority",
                            ""
                        )
                    )


                # --------------------------------------------
                # RIGHT SIDE
                # --------------------------------------------

                with col2:

                    st.write(
                        "**Department:**"
                    )

                    st.write(
                        incident.get(
                            "assigned_department",
                            "Not Assigned"
                        )
                    )


                    st.write(
                        "**Current Status:**"
                    )

                    st.write(
                        incident.get(
                            "status",
                            "OPEN"
                        )
                    )


                    st.write(
                        "**Created:**"
                    )

                    st.write(
                        incident.get(
                            "created_at",
                            ""
                        )
                    )


                    if incident.get(
                        "emergency"
                    ):

                        st.error(
                            "🚨 EMERGENCY INCIDENT"
                        )


                # --------------------------------------------
                # AI WHY
                # --------------------------------------------

                st.info(
                    "💡 WHY: " +
                    str(
                        incident.get(
                            "ai_explanation",
                            ""
                        )
                    )
                )


                # --------------------------------------------
                # ACTION
                # --------------------------------------------

                st.warning(
                    "🚨 ACTION: " +
                    str(
                        incident.get(
                            "recommended_action",
                            ""
                        )
                    )
                )


                # --------------------------------------------
                # INCIDENT PHOTO
                # --------------------------------------------

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


                # --------------------------------------------
                # STATUS UPDATE
                # --------------------------------------------

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


                # --------------------------------------------
                # DEPARTMENT UPDATE
                # --------------------------------------------

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


                # --------------------------------------------
                # UPDATE BUTTON
                # --------------------------------------------

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

    # IMPORTANT:
    # Dashboard code is kept inside dashboard.py.
    # This prevents dashboard variables such as `incidents`
    # from interfering with Report Incident.

    show_dashboard()