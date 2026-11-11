
import json
from urllib.request import urlopen
from urllib.error import URLError, HTTPError

import pandas as pd
import streamlit as st
from pathlib import Path

API_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="Data Quality Platform",
    page_icon="📊",
    layout="wide",
)


def fetch_api(endpoint):
    try:
        with urlopen(f"{API_URL}{endpoint}", timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except (URLError, HTTPError, TimeoutError) as error:
        st.error(f"API connection failed: {error}")
        return None


st.title("Configurable Data Quality Platform")
st.caption("Data quality monitoring, pipeline execution and quarantine management")

# API health
health = fetch_api("/health")

if not health:
    st.error("Start the FastAPI server before using this dashboard.")
    st.stop()

st.success("API connected | Database connected")

# Dashboard metrics
summary = fetch_api("/dashboard/summary")

if summary:
    st.subheader("Platform Overview")

    columns = st.columns(4)

    metrics = [
        ("Customers", summary["customers"]),
        ("Products", summary["products"]),
        ("Orders", summary["orders"]),
        ("Order Items", summary["order_items"]),
    ]

    for column, (label, value) in zip(columns, metrics):
        column.metric(label, f"{value:,}")

    columns = st.columns(2)
    columns[0].metric("Pipeline Runs", summary["pipeline_runs"])
    columns[1].metric(
        "Quarantined Records",
        summary["quarantined_records"],
    )

st.divider()

# Pipeline run history
st.subheader("Pipeline Run History")

runs = fetch_api("/runs")

if runs:
    runs_df = pd.DataFrame(runs)

    display_columns = [
        "dataset_name",
        "status",
        "input_records",
        "output_records",
        "rejected_records",
        "error_records",
        "started_at",
    ]

    st.dataframe(
        runs_df[display_columns],
        use_container_width=True,
        hide_index=True,
    )

    # Select a run for detailed inspection
    st.subheader("Run Details")

    selected_run = st.selectbox(
        "Select a pipeline run",
        runs,
        format_func=lambda run: (
            f"{run['dataset_name']} | {run['status']} | "
            f"{run['run_id'][:8]}"
        ),
    )

    run_id = selected_run["run_id"]

    validation_tab, quarantine_tab = st.tabs(
        ["Validation Results", "Quarantine Records"]
    )

    with validation_tab:
        validation_data = fetch_api(
            f"/runs/{run_id}/validations"
        )

        if validation_data:
            st.dataframe(
                pd.DataFrame(validation_data),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No validation results available for this run.")

    with quarantine_tab:
        quarantine_data = fetch_api(
            f"/runs/{run_id}/quarantine"
        )

        if quarantine_data:
            st.dataframe(
                pd.DataFrame(quarantine_data),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No quarantined records for this run.")

else:
    st.info("No pipeline runs available.")
    

# -----------------------------------------
# EDGE CASE AND REJECTION ANALYTICS
# -----------------------------------------

st.divider()
st.header("Data Quality Analytics")
st.caption("Analysis of the 30 labelled edge-case test scenarios")

analytics = fetch_api("/analytics/edge-cases")

if analytics:
    metric_cols = st.columns(4)

    metric_cols[0].metric(
        "Total Scenarios", analytics["total_scenarios"]
    )
    metric_cols[1].metric(
        "Tests Passed", analytics["passed"]
    )
    metric_cols[2].metric(
        "Accepted Fixtures", analytics["accepted"]
    )
    metric_cols[3].metric(
        "Rejected Fixtures", analytics["rejected"]
    )

    outcomes = pd.DataFrame(analytics["dataset_outcomes"])

    st.subheader("Dataset-wise Test Outcomes")

    if not outcomes.empty:
        outcome_chart = (
            outcomes.pivot(
                index="dataset_name",
                columns="actual_outcome",
                values="records",
            )
            .fillna(0)
        )

        st.bar_chart(outcome_chart)

    rejection_summary = pd.DataFrame(
        analytics["rejection_summary"]
    )

    st.subheader("Rejection Reasons")

    if not rejection_summary.empty:
        rejection_chart = (
            rejection_summary
            .groupby("rejection_reason")["rejected_records"]
            .sum()
            .sort_values(ascending=False)
        )

        st.bar_chart(rejection_chart)

    st.subheader("Rejected Record Investigation")

    details = pd.DataFrame(analytics["details"])
    rejected = details[
        details["actual_outcome"] == "REJECT"
    ].copy()

    available_datasets = sorted(
        rejected["dataset_name"].unique().tolist()
    )

    selected_dataset = st.selectbox(
        "Filter by dataset",
        ["All datasets"] + available_datasets,
        key="edge_dataset_filter",
    )

    if selected_dataset != "All datasets":
        rejected = rejected[
            rejected["dataset_name"] == selected_dataset
        ]

    if not rejected.empty:
        st.dataframe(
            rejected[
                [
                    "dataset_name",
                    "scenario",
                    "source_record_id",
                    "failed_rule_names",
                    "rejection_reason",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )

        selected_record = st.selectbox(
            "Inspect rejected record",
            rejected["source_record_id"].tolist(),
            key="rejected_record_selector",
        )

        record = rejected[
            rejected["source_record_id"] == selected_record
        ].iloc[0]

        st.write("**Scenario:**", record["scenario"])
        st.write("**Failed rules:**", record["failed_rule_names"])
        st.write("**Rejection reason:**", record["rejection_reason"])

        with st.expander("View original record data"):
            st.json(json.loads(record["record_data"]))

    else:
        st.info("No rejected records for this filter.")

else:
    st.warning("Edge-case analytics are currently unavailable.")


st.divider()
st.caption("Configurable Data Quality Platform | Version 1.0")
