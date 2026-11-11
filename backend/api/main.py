
from fastapi import FastAPI, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from backend.services.database import engine

import pandas as pd
import json
from pathlib import Path

app = FastAPI(
    title="Configurable Data Quality Platform",
    description="API for data quality validation, pipeline monitoring and quarantine records.",
    version="1.0.0",
)


@app.get("/")
def root():
    return {
        "message": "Data Quality Platform API",
        "status": "running",
    }


@app.get("/health")
def health():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "api": "healthy",
            "database": "connected",
        }
    except SQLAlchemyError:
        raise HTTPException(
            status_code=503,
            detail="Database connection failed",
        )


@app.get("/dashboard/summary")
def dashboard_summary():
    queries = {
        "customers": "SELECT COUNT(*) FROM ecommerce.customers",
        "products": "SELECT COUNT(*) FROM ecommerce.products",
        "orders": "SELECT COUNT(*) FROM ecommerce.orders",
        "order_items": "SELECT COUNT(*) FROM ecommerce.order_items",
        "pipeline_runs": "SELECT COUNT(*) FROM platform.pipeline_runs",
        "quarantined_records": "SELECT COUNT(*) FROM platform.quarantine_records",
    }

    try:
        with engine.connect() as connection:
            summary = {
                name: connection.execute(text(query)).scalar_one()
                for name, query in queries.items()
            }

        return summary

    except SQLAlchemyError as error:
        raise HTTPException(status_code=500, detail=str(error))


@app.get("/runs")
def get_pipeline_runs():
    query = text("""
        SELECT
            r.run_id,
            d.dataset_name,
            r.status,
            r.input_records,
            r.output_records,
            r.rejected_records,
            r.error_records,
            r.started_at,
            r.completed_at
        FROM platform.pipeline_runs r
        JOIN platform.datasets d
          ON d.dataset_id = r.dataset_id
        ORDER BY r.created_at DESC
    """)

    with engine.connect() as connection:
        rows = connection.execute(query).mappings().all()

    return [dict(row) for row in rows]


@app.get("/runs/{run_id}/validations")
def get_validation_results(run_id: str):
    query = text("""
    SELECT
        v.rule_id,
        r.rule_name,
        v.status,
        v.total_records,
        v.passed_records,
        v.failed_records,
        v.severity,
        v.execution_time_ms,
        v.failure_reason
    FROM platform.validation_results v
    JOIN platform.validation_rules r
        ON r.rule_id = v.rule_id
    WHERE v.run_id = :run_id
    ORDER BY v.created_at
""")

    with engine.connect() as connection:
        rows = connection.execute(
            query, {"run_id": run_id}
        ).mappings().all()

    if not rows:
        raise HTTPException(
            status_code=404,
            detail="No validation results found for this run",
        )

    return [dict(row) for row in rows]


@app.get("/runs/{run_id}/quarantine")
def get_quarantine_records(run_id: str):
    query = text("""
        SELECT
            quarantine_id,
            dataset_id,
            source_file,
            source_record_id,
            record_data,
            failed_rule_ids,
            rejection_reason,
            rejected_at
        FROM platform.quarantine_records
        WHERE run_id = :run_id
        ORDER BY rejected_at
    """)

    with engine.connect() as connection:
        rows = connection.execute(
            query, {"run_id": run_id}
        ).mappings().all()

    return [dict(row) for row in rows]


PROJECT_ROOT = Path(__file__).resolve().parents[2]


@app.get("/analytics/edge-cases")
def get_edge_case_analytics():
    detail_file = (
        PROJECT_ROOT / "reports" / "edge_case_rejection_analysis.csv"
    )
    summary_file = (
        PROJECT_ROOT / "reports" / "edge_case_rejection_summary.csv"
    )

    if not detail_file.exists() or not summary_file.exists():
        raise HTTPException(
            status_code=404,
            detail="Edge-case reports have not been generated.",
        )

    details = pd.read_csv(detail_file)
    rejection_summary = pd.read_csv(summary_file)

    outcomes = (
        details.groupby(
            ["dataset_name", "actual_outcome"]
        )
        .size()
        .reset_index(name="records")
    )

    return {
        "total_scenarios": int(len(details)),
        "passed": int(details["test_passed"].sum()),
        "failed": int((~details["test_passed"]).sum()),
        "accepted": int(
            (details["actual_outcome"] == "ACCEPT").sum()
        ),
        "rejected": int(
            (details["actual_outcome"] == "REJECT").sum()
        ),
        "dataset_outcomes": json.loads(
            outcomes.to_json(orient="records")
        ),
        "rejection_summary": json.loads(
            rejection_summary.to_json(orient="records")
        ),
        "details": json.loads(
            details.to_json(orient="records")
        ),
    }
