import os
import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Data Reliability Control Center",
    page_icon="🏛️",
    layout="wide",
)

SAMPLE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample_data")


@st.cache_data
def load_data():
    return {
        "datasets":  pd.read_csv(os.path.join(SAMPLE_DIR, "datasets.csv")),
        "rules":     pd.read_csv(os.path.join(SAMPLE_DIR, "rules.csv")),
        "runs":      pd.read_csv(os.path.join(SAMPLE_DIR, "rule_runs.csv")),
        "health":    pd.read_csv(os.path.join(SAMPLE_DIR, "health_scores.csv")),
        "incidents": pd.read_csv(os.path.join(SAMPLE_DIR, "incidents.csv")),
    }


data = load_data()

# ── Header ─────────────────────────────────────────────────────────────────────
st.title("🏛️ Data Reliability Control Center")
st.markdown(
    "**Monitor dataset health, rule failures, and governance incidents "
    "before bad data reaches dashboards.**"
)
st.divider()

# ── Tabs ───────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(
    ["📊 Overview", "📋 Dataset Registry", "🔍 Rule Runs", "🚨 Incidents"]
)

# ─── TAB 1: Overview ──────────────────────────────────────────────────────────
with tab1:
    health    = data["health"]
    incidents = data["incidents"]

    avg_health     = health["health_score"].mean()
    open_incidents = (incidents["status"] == "OPEN").sum()
    total_failed   = (data["runs"]["status"] == "FAILED").sum()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Datasets Monitored", len(health))
    c2.metric("Avg Health Score",   f"{avg_health:.0%}")
    c3.metric(
        "Open Incidents", open_incidents,
        f"{open_incidents} need attention",
        delta_color="inverse" if open_incidents > 0 else "normal",
    )
    c4.metric("Total Failed Runs (7d)", total_failed, delta_color="inverse")

    st.divider()
    st.subheader("Dataset Health")

    for _, row in health.iterrows():
        score    = row["health_score"]
        icon     = "🟢" if score >= 0.9 else ("🟡" if score >= 0.75 else "🔴")
        ds_inc   = incidents[incidents["dataset_id"] == row["dataset_id"]]
        open_cnt = int((ds_inc["status"] == "OPEN").sum())

        label = f"{icon} **{row['dataset_name']}** — Health: {score:.0%}"
        if open_cnt > 0:
            label += f"  🚨 {open_cnt} open incident(s)"

        with st.expander(label):
            m1, m2, m3 = st.columns(3)
            m1.metric("Health Score",  f"{score:.0%}")
            m2.metric("Rules Passed",  f"{int(row['passed_runs'])}/{int(row['total_runs'])}")
            m3.metric("Failed Runs",   int(row["failed_runs"]))

            open_ds_inc = ds_inc[ds_inc["status"] == "OPEN"]
            for _, inc in open_ds_inc.iterrows():
                st.error(f"**{inc['title']}**  \n{inc['explanation']}")

# ─── TAB 2: Dataset Registry ──────────────────────────────────────────────────
with tab2:
    st.subheader("Registered Datasets")

    ds_view = data["datasets"].merge(
        data["health"][["dataset_id","health_score","total_runs","failed_runs"]],
        on="dataset_id", how="left",
    )
    ds_view["health_score"] = ds_view["health_score"].map(lambda x: f"{x:.0%}")
    ds_view["failed_runs"]  = ds_view["failed_runs"].fillna(0).astype(int)

    st.dataframe(
        ds_view[["dataset_id","name","owner","tier","tags","health_score","total_runs","failed_runs"]],
        use_container_width=True, hide_index=True,
    )

    st.divider()
    st.subheader("Data Quality Rules")
    st.dataframe(data["rules"], use_container_width=True, hide_index=True)

# ─── TAB 3: Rule Runs ─────────────────────────────────────────────────────────
with tab3:
    st.subheader("Rule Run History (Last 7 Days)")

    runs = data["runs"].copy()
    runs["run_at"] = pd.to_datetime(runs["run_at"]).dt.strftime("%Y-%m-%d %H:%M")

    f_status  = st.selectbox("Filter by Status",  ["All", "PASSED", "FAILED"])
    f_dataset = st.selectbox("Filter by Dataset", ["All"] + list(data["datasets"]["dataset_id"].unique()))

    filtered = runs.copy()
    if f_status  != "All": filtered = filtered[filtered["status"]     == f_status]
    if f_dataset != "All": filtered = filtered[filtered["dataset_id"] == f_dataset]

    st.dataframe(
        filtered[["run_id","rule_id","dataset_id","status","run_at","actual","message"]],
        use_container_width=True, hide_index=True,
    )

    r1, r2 = st.columns(2)
    r1.metric("Runs shown", len(filtered))
    r2.metric("Failed",     (filtered["status"] == "FAILED").sum())

# ─── TAB 4: Incidents ─────────────────────────────────────────────────────────
with tab4:
    st.subheader("Governance Incidents")

    incidents = data["incidents"].copy()
    incidents["detected_at"] = pd.to_datetime(incidents["detected_at"]).dt.strftime("%Y-%m-%d %H:%M")

    open_inc     = incidents[incidents["status"] == "OPEN"]
    resolved_inc = incidents[incidents["status"] == "RESOLVED"]

    if not open_inc.empty:
        st.markdown("#### 🚨 Open Incidents")
        for _, inc in open_inc.iterrows():
            header = f"**[{inc['severity'].upper()}]** {inc['title']} — {inc['detected_at']}"
            with st.expander(header):
                st.markdown(f"**Dataset:** `{inc['dataset_id']}` | **Rule:** `{inc['rule_id']}`")
                st.markdown(f"**Explanation:**  \n{inc['explanation']}")
                st.download_button(
                    "⬇️ Download Incident Report",
                    data=(
                        f"INCIDENT: {inc['title']}\n\n"
                        f"{inc['explanation']}\n\n"
                        f"Detected: {inc['detected_at']}\nStatus: {inc['status']}"
                    ),
                    file_name=f"incident_{inc['incident_id']}.txt",
                    key=inc["incident_id"],
                )

    if not resolved_inc.empty:
        st.markdown("#### ✅ Resolved Incidents")
        for _, inc in resolved_inc.iterrows():
            with st.expander(f"~~{inc['title']}~~ — resolved"):
                st.markdown(inc["explanation"])