import streamlit as st
import pandas as pd
from database import get_all_incidents


def show_hotspot_detection():

    st.title("🔥 Campus Hotspot Detection")
    st.caption(
        "AI-powered identification of locations with frequent and high-risk incidents."
    )

    # =========================================================
    # LOAD INCIDENT DATA
    # =========================================================

    incidents = get_all_incidents()

    if not incidents:
        st.info(
            "No incidents are available yet. "
            "Report incidents to generate hotspot intelligence."
        )
        return

    data = [dict(incident) for incident in incidents]

    df = pd.DataFrame(data)

    # =========================================================
    # CHECK LOCATION DATA
    # =========================================================

    if "location" not in df.columns:

        st.warning(
            "⚠️ Incident location data is not available."
        )
        return

    df["location"] = (
        df["location"]
        .fillna("Unknown")
        .astype(str)
        .str.strip()
    )

    df = df[df["location"] != ""]

    if df.empty:

        st.info(
            "📍 No valid incident locations are available."
        )
        return

    # =========================================================
    # PREPARE RISK SCORE
    # =========================================================

    if "risk_score" in df.columns:

        df["risk_score"] = pd.to_numeric(
            df["risk_score"],
            errors="coerce"
        ).fillna(0)

    else:

        df["risk_score"] = 0

    # =========================================================
    # HOTSPOT ANALYSIS
    # =========================================================

    hotspot_df = (
        df.groupby("location")
        .agg(
            Incidents=("location", "count"),
            Average_Risk=("risk_score", "mean"),
            Maximum_Risk=("risk_score", "max")
        )
        .reset_index()
    )

    hotspot_df = hotspot_df.rename(
        columns={
            "location": "Location",
            "Average_Risk": "Average Risk",
            "Maximum_Risk": "Maximum Risk"
        }
    )

    hotspot_df["Average Risk"] = (
        hotspot_df["Average Risk"]
        .round(0)
        .astype(int)
    )

    hotspot_df["Maximum Risk"] = (
        hotspot_df["Maximum Risk"]
        .round(0)
        .astype(int)
    )

    # =========================================================
    # HOTSPOT SCORE
    # =========================================================

    hotspot_df["Hotspot Score"] = (
        hotspot_df["Incidents"] * 10
        + hotspot_df["Average Risk"] * 0.5
        + hotspot_df["Maximum Risk"] * 0.3
    ).round(0)

    hotspot_df = hotspot_df.sort_values(
        "Hotspot Score",
        ascending=False
    )

    # =========================================================
    # HOTSPOT LEVEL
    # =========================================================

    def get_hotspot_level(score):

        if score >= 80:
            return "🔴 CRITICAL"

        elif score >= 50:
            return "🟠 HIGH"

        elif score >= 25:
            return "🟡 MODERATE"

        else:
            return "🟢 LOW"

    hotspot_df["Hotspot Level"] = (
        hotspot_df["Hotspot Score"]
        .apply(get_hotspot_level)
    )

    # =========================================================
    # SUMMARY METRICS
    # =========================================================

    st.subheader("📊 Hotspot Intelligence")

    total_locations = len(hotspot_df)

    critical_hotspots = len(
        hotspot_df[
            hotspot_df["Hotspot Level"] == "🔴 CRITICAL"
        ]
    )

    high_hotspots = len(
        hotspot_df[
            hotspot_df["Hotspot Level"] == "🟠 HIGH"
        ]
    )

    top_hotspot = hotspot_df.iloc[0]["Location"]

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "📍 Locations",
            total_locations
        )

    with col2:
        st.metric(
            "🔴 Critical Hotspots",
            critical_hotspots
        )

    with col3:
        st.metric(
            "🟠 High Hotspots",
            high_hotspots
        )

    with col4:
        st.metric(
            "🔥 Top Hotspot",
            top_hotspot
        )

    st.divider()

    # =========================================================
    # TOP HOTSPOT
    # =========================================================

    st.subheader("🔥 Highest-Risk Campus Hotspot")

    top_row = hotspot_df.iloc[0]

    st.error(
        f"🔥 **{top_row['Location']}** is currently the "
        f"highest-priority hotspot.\n\n"
        f"📊 Incidents: **{top_row['Incidents']}**\n\n"
        f"⚠️ Average Risk: **{top_row['Average Risk']}/100**\n\n"
        f"🚨 Maximum Risk: **{top_row['Maximum Risk']}/100**"
    )

    # =========================================================
    # HOTSPOT TABLE
    # =========================================================

    st.subheader("📋 Campus Hotspot Analysis")

    display_columns = [
        "Location",
        "Incidents",
        "Average Risk",
        "Maximum Risk",
        "Hotspot Score",
        "Hotspot Level"
    ]

    st.dataframe(
        hotspot_df[display_columns],
        use_container_width=True,
        hide_index=True
    )

    # =========================================================
    # INCIDENT FREQUENCY CHART
    # =========================================================

    st.subheader("📊 Incidents by Location")

    chart_df = (
        hotspot_df
        .set_index("Location")["Incidents"]
        .head(10)
    )

    st.bar_chart(chart_df)

    # =========================================================
    # RISK CHART
    # =========================================================

    st.subheader("⚠️ Average Risk by Location")

    risk_chart = (
        hotspot_df
        .set_index("Location")["Average Risk"]
        .head(10)
    )

    st.bar_chart(risk_chart)

    # =========================================================
    # AI SAFETY RECOMMENDATION
    # =========================================================

    st.divider()

    st.subheader("🤖 AI Hotspot Recommendation")

    if critical_hotspots > 0:

        st.error(
            f"🚨 **Immediate attention required.** "
            f"{critical_hotspots} critical hotspot(s) have been detected. "
            "Campus security should prioritize these locations."
        )

    elif high_hotspots > 0:

        st.warning(
            f"⚠️ **Increased monitoring recommended.** "
            f"{high_hotspots} high-risk hotspot(s) have been detected."
        )

    else:

        st.success(
            "✅ No critical campus hotspots detected. "
            "Continue routine monitoring."
        )

    st.info(
        f"📍 Current highest-priority location: "
        f"**{top_hotspot}**"
    )


# =============================================================
# TEST
# =============================================================

if __name__ == "__main__":
    show_hotspot_detection()