import streamlit as st
import pandas as pd
from database import get_all_incidents
from emergency import generate_emergency_response


def show_dashboard():

    st.title("📊 CampusGuardian AI Dashboard")
    st.caption("AI-powered campus safety monitoring and incident intelligence")

    # =========================================================
    # LOAD DATA
    # =========================================================

    incidents = get_all_incidents()

    if not incidents:
        st.info("No incidents have been reported yet.")
        st.write("Go to **Report Incident** and create your first incident.")
        return

    data = []

    for incident in incidents:
        data.append(dict(incident))

    df = pd.DataFrame(data)

    # =========================================================
    # CLEAN DATA
    # =========================================================

    for column in ["risk_score", "latitude", "longitude"]:
        if column in df.columns:
            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            )

    if "created_at" in df.columns:
        df["created_at"] = pd.to_datetime(
            df["created_at"],
            errors="coerce"
        )

    # =========================================================
    # DASHBOARD METRICS
    # =========================================================

    total_incidents = len(df)

    critical_incidents = 0
    high_incidents = 0
    open_incidents = 0
    resolved_incidents = 0

    if "risk_level" in df.columns:

        critical_incidents = len(
            df[
                df["risk_level"]
                .fillna("")
                .astype(str)
                .str.upper()
                == "CRITICAL"
            ]
        )

        high_incidents = len(
            df[
                df["risk_level"]
                .fillna("")
                .astype(str)
                .str.upper()
                == "HIGH"
            ]
        )

    if "status" in df.columns:

        status_upper = (
            df["status"]
            .fillna("")
            .astype(str)
            .str.upper()
        )

        open_incidents = len(
            df[
                status_upper.isin(
                    ["OPEN", "ASSIGNED", "IN PROGRESS"]
                )
            ]
        )

        resolved_incidents = len(
            df[
                status_upper == "RESOLVED"
            ]
        )

    # =========================================================
    # SAFETY OVERVIEW
    # =========================================================

    st.subheader("📌 Safety Overview")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Total Incidents",
            total_incidents
        )

    with col2:
        st.metric(
            "🔴 Critical",
            critical_incidents
        )

    with col3:
        st.metric(
            "🟠 High Risk",
            high_incidents
        )

    with col4:
        st.metric(
            "✅ Resolved",
            resolved_incidents
        )

    st.divider()

    # =========================================================
    # RISK DISTRIBUTION
    # =========================================================

    st.subheader("🚨 Risk Distribution")

    if "risk_level" in df.columns:

        risk_counts = (
            df["risk_level"]
            .fillna("UNKNOWN")
            .astype(str)
            .str.upper()
            .value_counts()
        )

        st.bar_chart(risk_counts)

    # =========================================================
    # INCIDENT CATEGORIES
    # =========================================================

    st.subheader("📂 Incident Categories")

    if "category" in df.columns:

        category_counts = (
            df["category"]
            .fillna("Unknown")
            .astype(str)
            .value_counts()
        )

        st.bar_chart(category_counts)

    # =========================================================
    # STATUS DISTRIBUTION
    # =========================================================

    st.subheader("🔄 Incident Status")

    if "status" in df.columns:

        status_counts = (
            df["status"]
            .fillna("UNKNOWN")
            .astype(str)
            .value_counts()
        )

        st.bar_chart(status_counts)

    # =========================================================
    # DEPARTMENT WORKLOAD
    # =========================================================

    st.subheader("🏢 Department Workload")

    if "assigned_department" in df.columns:

        department_counts = (
            df["assigned_department"]
            .fillna("Unassigned")
            .astype(str)
            .value_counts()
        )

        st.bar_chart(department_counts)

    # =========================================================
    # HIGH PRIORITY INCIDENTS
    # =========================================================

    st.subheader("⚠️ High Priority Incidents")

    if "risk_score" in df.columns:

        high_risk_df = df[
            df["risk_score"].fillna(0) >= 50
        ].copy()

        if not high_risk_df.empty:

            columns_to_show = []

            for column in [
                "id",
                "title",
                "category",
                "location",
                "risk_score",
                "risk_level",
                "priority",
                "assigned_department",
                "status"
            ]:

                if column in high_risk_df.columns:
                    columns_to_show.append(column)

            st.dataframe(
                high_risk_df[columns_to_show],
                use_container_width=True,
                hide_index=True
            )

        else:

            st.success(
                "No high-risk incidents detected."
            )

    # =========================================================
    # CAMPUS RISK TREND
    # =========================================================

    st.divider()

    st.subheader("📈 Campus Risk Trend")

    if "created_at" in df.columns and "risk_score" in df.columns:

        trend_df = df[
            ["created_at", "risk_score"]
        ].dropna().copy()

        if not trend_df.empty:

            trend_df = trend_df.sort_values("created_at")

            trend_df = trend_df.set_index("created_at")

            trend_df = trend_df.rename(
                columns={
                    "risk_score": "Risk Score"
                }
            )

            st.line_chart(
    trend_df,
    width="stretch"
)

            latest_risk = float(
                trend_df["Risk Score"].iloc[-1]
            )

            average_risk = float(
                trend_df["Risk Score"].mean()
            )

            highest_risk = float(
                trend_df["Risk Score"].max()
            )

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric(
                    "Latest Risk",
                    f"{latest_risk:.0f}/100"
                )

            with col2:
                st.metric(
                    "Average Risk",
                    f"{average_risk:.0f}/100"
                )

            with col3:
                st.metric(
                    "Highest Risk",
                    f"{highest_risk:.0f}/100"
                )

        else:

            st.info(
                "Not enough data available for the risk trend."
            )

    # =========================================================
    # RECENT INCIDENTS
    # =========================================================

    st.divider()

    st.subheader("🕒 Recent Incidents")

    recent_df = df.copy()

    if "created_at" in recent_df.columns:
        recent_df = recent_df.sort_values(
            "created_at",
            ascending=False
        )

    recent_df = recent_df.head(10)

    columns_to_show = []

    for column in [
        "title",
        "category",
        "location",
        "assigned_department",
        "risk_score",
        "risk_level",
        "status",
        "created_at"
    ]:

        if column in recent_df.columns:
            columns_to_show.append(column)

    if columns_to_show:

        display_df = recent_df[columns_to_show].copy()

        rename_columns = {
            "title": "Incident",
            "category": "Category",
            "location": "Location",
            "assigned_department": "Department",
            "risk_score": "Risk",
            "risk_level": "Risk Level",
            "status": "Status",
            "created_at": "Time"
        }

        display_df = display_df.rename(
            columns=rename_columns
        )

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )

    # =========================================================
    # RESOLUTION PERFORMANCE
    # =========================================================

    st.divider()

    st.subheader("📈 Resolution Performance")

    resolution_percentage = 0

    if total_incidents > 0:

        resolution_percentage = (
            resolved_incidents /
            total_incidents
        ) * 100

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Total Incidents",
            total_incidents
        )

    with col2:
        st.metric(
            "Total Resolved",
            resolved_incidents
        )

    with col3:
        st.metric(
            "Resolution Rate",
            f"{resolution_percentage:.1f}%"
        )

    # Open vs Resolved chart

    open_resolved_data = pd.DataFrame(
        {
            "Status": [
                "Active",
                "Resolved"
            ],
            "Count": [
                open_incidents,
                resolved_incidents
            ]
        }
    )

    st.bar_chart(
        open_resolved_data.set_index("Status")
    )

    # =========================================================
    # CAMPUS HOTSPOT SUMMARY
    # =========================================================

    st.divider()

    st.subheader("🔥 Campus Hotspot Summary")

    if "location" in df.columns:

        hotspot_df = df.copy()

        hotspot_df["location"] = (
            hotspot_df["location"]
            .fillna("Unknown")
            .astype(str)
            .str.strip()
        )

        hotspot_df = hotspot_df[
            hotspot_df["location"] != ""
        ]

        if not hotspot_df.empty:

            hotspot_counts = (
                hotspot_df["location"]
                .value_counts()
                .reset_index()
            )

            hotspot_counts.columns = [
                "Location",
                "Incidents"
            ]

            if "risk_score" in hotspot_df.columns:

                average_risk = (
                    hotspot_df
                    .groupby("location")["risk_score"]
                    .mean()
                    .reset_index()
                )

                average_risk.columns = [
                    "Location",
                    "Average Risk"
                ]

                hotspot_counts = hotspot_counts.merge(
                    average_risk,
                    on="Location",
                    how="left"
                )

                hotspot_counts["Average Risk"] = (
                    hotspot_counts["Average Risk"]
                    .round(0)
                    .astype(int)
                )

            hotspot_counts = hotspot_counts.head(10)

            st.dataframe(
                hotspot_counts,
                use_container_width=True,
                hide_index=True
            )

        else:

            st.info(
                "No campus hotspot data available."
            )

    # =========================================================
    # AI CAMPUS SAFETY INSIGHTS
    # =========================================================

    st.divider()

    st.subheader("🤖 AI Campus Safety Insights")

    insights = []

    # ---------------------------------------------------------
    # Highest-risk category
    # ---------------------------------------------------------

    if "category" in df.columns and "risk_score" in df.columns:

        category_risk = (
            df.groupby("category")["risk_score"]
            .mean()
            .sort_values(ascending=False)
        )

        if not category_risk.empty:

            top_category = category_risk.index[0]
            top_category_risk = category_risk.iloc[0]

            insights.append(
                f"🔴 **{top_category}** currently has the "
                f"highest average risk score "
                f"({top_category_risk:.0f}/100)."
            )

    # ---------------------------------------------------------
    # Highest-risk department
    # ---------------------------------------------------------

    if (
        "assigned_department" in df.columns
        and "risk_score" in df.columns
    ):

        department_risk = (
            df.groupby("assigned_department")["risk_score"]
            .mean()
            .sort_values(ascending=False)
        )

        if not department_risk.empty:

            top_department = department_risk.index[0]
            top_department_risk = department_risk.iloc[0]

            insights.append(
                f"🏢 **{top_department}** is currently "
                f"responsible for the highest average-risk "
                f"incidents ({top_department_risk:.0f}/100)."
            )

    # ---------------------------------------------------------
    # Unresolved high-risk incidents
    # ---------------------------------------------------------

    if "risk_score" in df.columns and "status" in df.columns:

        active_high_risk = df[
            (df["risk_score"].fillna(0) >= 50)
            &
            (
                ~df["status"]
                .fillna("")
                .astype(str)
                .str.upper()
                .eq("RESOLVED")
            )
        ]

        if len(active_high_risk) > 0:

            insights.append(
                f"⚠️ There are **{len(active_high_risk)} "
                f"unresolved high-risk incident(s)**. "
                "These should be prioritized by the responsible departments."
            )

    # ---------------------------------------------------------
    # Emergency incidents
    # ---------------------------------------------------------

    if "emergency" in df.columns:

        emergency_count = (
            pd.to_numeric(
                df["emergency"],
                errors="coerce"
            )
            .fillna(0)
            .sum()
        )

        if emergency_count > 0:

            insights.append(
                f"🚨 **{int(emergency_count)} emergency "
                f"incident(s)** have been reported. "
                "Emergency incidents should receive immediate attention."
            )

    # ---------------------------------------------------------
    # Display insights
    # ---------------------------------------------------------

    if insights:

        for insight in insights:
            st.info(insight)

    else:

        st.success(
            "✅ No major safety patterns detected from the current incident data."
        )

    # =========================================================
    # AI SAFETY SUMMARY
    # =========================================================

    st.divider()

    st.subheader("🧠 AI Safety Summary")

    if critical_incidents > 0:

        st.error(
            f"🚨 {critical_incidents} critical incident(s) "
            "require immediate attention."
        )

    elif high_incidents > 0:

        st.warning(
            f"⚠️ {high_incidents} high-risk incident(s) "
            "should be reviewed by the responsible department."
        )

    else:

        st.success(
            "✅ No critical or high-risk incidents currently detected."
        )

    st.info(
        f"📌 Currently active incidents: **{open_incidents}**"
    )

        # ============================================================
    # RISK TREND PREDICTION
    # ============================================================

    st.divider()

    st.subheader("📈 Risk Trend Prediction")

    total_incidents = len(incidents)

    if total_incidents == 0:
        st.info("No incident data available for risk prediction.")
    else:
        critical_count = sum(
            1 for incident in incidents
            if str(incident.get("risk_level", "")).upper() == "CRITICAL"
        )

        high_count = sum(
            1 for incident in incidents
            if str(incident.get("risk_level", "")).upper() == "HIGH"
        )

        medium_count = sum(
            1 for incident in incidents
            if str(incident.get("risk_level", "")).upper() == "MEDIUM"
        )

        low_count = sum(
            1 for incident in incidents
            if str(incident.get("risk_level", "")).upper() == "LOW"
        )

        risk_points = (
            critical_count * 4
            + high_count * 3
            + medium_count * 2
            + low_count
        )

        if risk_points >= 12:
            prediction = "🔴 HIGH RISK"
            message = "Risk is increasing. Immediate attention is recommended."
        elif risk_points >= 6:
            prediction = "🟠 MODERATE RISK"
            message = "Risk is moderate. Continue monitoring incidents."
        else:
            prediction = "🟢 LOW RISK"
            message = "Risk is currently low."

        col1, col2 = st.columns(2)

        with col1:
            st.metric(
                "Current Incidents",
                total_incidents
            )

        with col2:
            st.metric(
                "Risk Score",
                risk_points
            )

        st.success(
            f"### Prediction: {prediction}\n\n{message}"
        )
            # ============================================================
    # TASK 8 — WHAT SHOULD WE DO NOW?
    # ============================================================

    st.divider()

    st.subheader("🤖 What Should We Do Now?")
    st.caption(
        "AI-assisted decision support for prioritizing the current campus safety situation."
    )

    # ------------------------------------------------------------
    # ANALYZE CURRENT CAMPUS SITUATION
    # ------------------------------------------------------------

    total_current = len(df)

    high_risk_count = 0
    emergency_count = 0
    unresolved_count = 0

    if "risk_score" in df.columns:
        high_risk_count = int(
            (pd.to_numeric(df["risk_score"], errors="coerce").fillna(0) >= 70).sum()
        )

    # Check emergency incidents
    if "is_emergency" in df.columns:
        emergency_values = df["is_emergency"].astype(str).str.lower()
        emergency_count = int(
            emergency_values.isin(
                ["true", "1", "yes", "y", "emergency"]
            ).sum()
        )
    elif "emergency" in df.columns:
        emergency_values = df["emergency"].astype(str).str.lower()
        emergency_count = int(
            emergency_values.isin(
                ["true", "1", "yes", "y", "emergency"]
            ).sum()
        )

    # Check unresolved incidents
    if "status" in df.columns:
        status_values = df["status"].astype(str).str.upper()
        unresolved_count = int(
            (~status_values.isin(["RESOLVED", "CLOSED"])).sum()
        )
    else:
        unresolved_count = total_current

    # ------------------------------------------------------------
    # GENERATE RECOMMENDED ACTIONS
    # ------------------------------------------------------------

    actions = []

    if emergency_count > 0:
        actions.append(
            "🚨 **Immediately prioritize all emergency incidents and alert the appropriate emergency response team.**"
        )

    if high_risk_count > 0:
        actions.append(
            f"🔴 **Prioritize the {high_risk_count} high-risk incident(s) for immediate security attention.**"
        )

    if unresolved_count > 0:
        actions.append(
            f"📌 **Assign and follow up on {unresolved_count} unresolved incident(s).**"
        )

    if total_current > 0:
        actions.append(
            "📊 **Continue monitoring the campus dashboard and risk trend for changes.**"
        )

    if not actions:
        actions.append(
            "✅ **No immediate high-risk action is required. Continue routine campus monitoring.**"
        )

    # ------------------------------------------------------------
    # DISPLAY DECISION SUPPORT
    # ------------------------------------------------------------

    if emergency_count > 0 or high_risk_count >= 3:
        st.error(
            "🚨 **IMMEDIATE ACTION REQUIRED**\n\n"
            "The current campus situation contains significant safety risks."
        )
    elif high_risk_count > 0:
        st.warning(
            "⚠️ **PRIORITY ACTION REQUIRED**\n\n"
            "High-risk incidents require attention from the responsible teams."
        )
    else:
        st.success(
            "✅ **NORMAL MONITORING**\n\n"
            "No critical action is currently required."
        )

    st.markdown("### 📋 Recommended Actions")

    for number, action in enumerate(actions, start=1):
        st.markdown(f"**{number}.** {action}")

    # ------------------------------------------------------------
    # CURRENT SITUATION SUMMARY
    # ------------------------------------------------------------

    st.markdown("### 📊 Current Situation")

    action_col1, action_col2, action_col3 = st.columns(3)

    with action_col1:
        st.metric(
            "Total Incidents",
            total_current
        )

    with action_col2:
        st.metric(
            "High-Risk Incidents",
            high_risk_count
        )

    with action_col3:
        st.metric(
            "Emergency Incidents",
            emergency_count
        )
            # ============================================================
    # TASK 9 — CAMPUS RISK MAP
    # ============================================================

    st.divider()

    st.subheader("🗺️ Campus Risk Map")
    st.caption(
        "Visual map showing reported incidents and their risk levels across campus."
    )

    # ------------------------------------------------------------
    # CHECK LOCATION DATA
    # ------------------------------------------------------------

    if "latitude" in df.columns and "longitude" in df.columns:

        map_df = df[
            ["latitude", "longitude"]
            + (
                ["risk_score"]
                if "risk_score" in df.columns
                else []
            )
        ].copy()

        # Convert coordinates to numbers
        map_df["latitude"] = pd.to_numeric(
            map_df["latitude"],
            errors="coerce"
        )

        map_df["longitude"] = pd.to_numeric(
            map_df["longitude"],
            errors="coerce"
        )

        # Remove invalid coordinates
        map_df = map_df.dropna(
            subset=["latitude", "longitude"]
        )

        if not map_df.empty:

            st.map(
                map_df[
                    ["latitude", "longitude"]
                ],
                latitude="latitude",
                longitude="longitude",
                size=100
            )

            st.success(
                f"📍 {len(map_df)} incident location(s) "
                "are currently displayed on the campus map."
            )

        else:

            st.info(
                "📍 No valid incident locations are available "
                "for the risk map."
            )

    else:

        st.warning(
            "⚠️ Latitude and longitude data are not available "
            "in the incident database."
        )
        
