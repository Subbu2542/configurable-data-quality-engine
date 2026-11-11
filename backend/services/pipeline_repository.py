import json
from uuid import UUID

import pandas as pd
from sqlalchemy import text

from backend.services.database import engine


def _json_safe(value):
    """Convert pandas/numpy values into JSON-compatible Python values."""
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}

    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]

    if value is None:
        return None

    try:
        missing = pd.isna(value)
        if isinstance(missing, bool) and missing:
            return None
    except (TypeError, ValueError):
        pass

    if hasattr(value, "item"):
        try:
            return value.item()
        except (ValueError, TypeError):
            pass

    return value


def _json_text(value):
    return json.dumps(_json_safe(value), allow_nan=False, default=str)


def create_pipeline_run(dataset_name, source_file, source_fingerprint, idempotency_key):
    """Create a RUNNING record, or return the existing record for this key."""

    with engine.begin() as connection:
        dataset = connection.execute(
            text("""
                SELECT dataset_id
                FROM platform.datasets
                WHERE dataset_name = :dataset_name
                  AND is_active = TRUE
            """),
            {"dataset_name": dataset_name},
        ).mappings().first()

        if not dataset:
            raise ValueError(f"Active dataset not found: {dataset_name}")

        dataset_id = dataset["dataset_id"]

        existing = connection.execute(
            text("""
                SELECT run_id, status, source_fingerprint
                FROM platform.pipeline_runs
                WHERE dataset_id = :dataset_id
                  AND idempotency_key = :idempotency_key
            """),
            {
                "dataset_id": dataset_id,
                "idempotency_key": idempotency_key,
            },
        ).mappings().first()

        if existing:
            if existing["source_fingerprint"] != source_fingerprint:
                raise ValueError(
                    "Idempotency key already exists for a different source file."
                )

            return {
                "run_id": str(existing["run_id"]),
                "dataset_id": str(dataset_id),
                "is_new": False,
                "status": existing["status"],
            }

        run_id = connection.execute(
            text("""
                INSERT INTO platform.pipeline_runs (
                    dataset_id,
                    idempotency_key,
                    source_file,
                    source_fingerprint,
                    status,
                    started_at
                )
                VALUES (
                    :dataset_id,
                    :idempotency_key,
                    :source_file,
                    :source_fingerprint,
                    'RUNNING',
                    CURRENT_TIMESTAMP
                )
                RETURNING run_id
            """),
            {
                "dataset_id": dataset_id,
                "idempotency_key": idempotency_key,
                "source_file": source_file,
                "source_fingerprint": source_fingerprint,
            },
        ).scalar_one()

        connection.execute(
            text("""
                INSERT INTO platform.pipeline_logs (
                    run_id, log_level, stage, message
                )
                VALUES (
                    :run_id, 'INFO', 'INGESTION',
                    :message
                )
            """),
            {
                "run_id": run_id,
                "message": f"Pipeline run started for {dataset_name}.",
            },
        )

        return {
            "run_id": str(run_id),
            "dataset_id": str(dataset_id),
            "is_new": True,
            "status": "RUNNING",
        }



def save_validation_outputs(
    run_id,
    dataset_id,
    dataset_name,
    source_file,
    input_records,
    validation_results,
    rejected_records,
):
    """Persist validation summaries, quarantined records, and run totals."""

    rejected_rows = rejected_records.to_dict(orient="records")
    rejected_count = len(rejected_rows)
    output_count = input_records - rejected_count
    final_status = "PARTIAL_SUCCESS" if rejected_count else "SUCCESS"

    with engine.begin() as connection:

        for result in validation_results:
            connection.execute(
                text("""
                    INSERT INTO platform.validation_results (
                        run_id, rule_id, status, total_records,
                        passed_records, failed_records, severity,
                        execution_time_ms, failure_reason
                    )
                    VALUES (
                        :run_id, :rule_id, :status, :total_records,
                        :passed_records, :failed_records, :severity,
                        :execution_time_ms, :failure_reason
                    )
                """),
                {
                    "run_id": run_id,
                    "rule_id": result["rule_id"],
                    "status": result["status"],
                    "total_records": result["total_records"],
                    "passed_records": result["passed_records"],
                    "failed_records": result["failed_records"],
                    "severity": result["severity"],
                    "execution_time_ms": result.get("execution_time_ms", 0),
                    "failure_reason": result.get("failure_reason"),
                },
            )

        for rejected in rejected_rows:
            record_data = {
                key: value
                for key, value in rejected.items()
                if key not in {
                    "source_file",
                    "source_record_id",
                    "failed_rule_ids",
                    "rejection_reason",
                }
            }

            connection.execute(
                text("""
                    INSERT INTO platform.quarantine_records (
                        run_id, dataset_id, source_file, source_record_id,
                        record_data, failed_rule_ids, rejection_reason
                    )
                    VALUES (
                        :run_id, :dataset_id, :source_file, :source_record_id,
                        CAST(:record_data AS JSONB),
                        CAST(:failed_rule_ids AS JSONB), :rejection_reason
                    )
                    ON CONFLICT (run_id, source_record_id) DO NOTHING
                """),
                {
                    "run_id": run_id,
                    "dataset_id": dataset_id,
                    "source_file": source_file,
                    "source_record_id": rejected["source_record_id"],
                    "record_data": _json_text(record_data),
                    "failed_rule_ids": _json_text(
                        rejected.get("failed_rule_ids", [])
                    ),
                    "rejection_reason": rejected["rejection_reason"],
                },
            )

        connection.execute(
            text("""
                UPDATE platform.pipeline_runs
                SET status = :status,
                    input_records = :input_records,
                    output_records = :output_records,
                    rejected_records = :rejected_records,
                    error_records = 0,
                    completed_at = CURRENT_TIMESTAMP
                WHERE run_id = :run_id
            """),
            {
                "run_id": run_id,
                "status": final_status,
                "input_records": input_records,
                "output_records": output_count,
                "rejected_records": rejected_count,
            },
        )

        connection.execute(
            text("""
                INSERT INTO platform.pipeline_logs (
                    run_id, log_level, stage, message
                )
                VALUES (
                    :run_id, :log_level, 'VALIDATION', :message
                )
            """),
            {
                "run_id": run_id,
                "log_level": "WARNING" if rejected_count else "INFO",
                "message": (
                    f"{dataset_name}: {input_records} input, "
                    f"{output_count} accepted, {rejected_count} quarantined."
                ),
            },
        )

    return {
        "run_id": str(run_id),
        "dataset": dataset_name,
        "status": final_status,
        "input_records": input_records,
        "output_records": output_count,
        "rejected_records": rejected_count,
    }

    
def publish_customers(accepted_records, run_id):
    """Publish accepted customer records with source lineage."""

    if accepted_records.empty:
        return 0

    records = accepted_records.copy()
    records = records.where(pd.notna(records), None)

    with engine.begin() as connection:
        for record in records.to_dict(orient="records"):
            connection.execute(
                text("""
                    INSERT INTO ecommerce.customers (
                        customer_id,
                        customer_name,
                        email,
                        phone,
                        city,
                        created_at,
                        updated_at,
                        source_file,
                        source_record_id,
                        run_id
                    )
                    VALUES (
                        :customer_id,
                        :customer_name,
                        :email,
                        :phone,
                        :city,
                        :created_at,
                        :updated_at,
                        :source_file,
                        :source_record_id,
                        :run_id
                    )
                    ON CONFLICT (customer_id)
                    DO UPDATE SET
                        customer_name = EXCLUDED.customer_name,
                        email = EXCLUDED.email,
                        phone = EXCLUDED.phone,
                        city = EXCLUDED.city,
                        updated_at = EXCLUDED.updated_at,
                        source_file = EXCLUDED.source_file,
                        source_record_id = EXCLUDED.source_record_id,
                        run_id = EXCLUDED.run_id,
                        ingested_at = CURRENT_TIMESTAMP
                """),
                {
                    **record,
                    "run_id": run_id,
                },
            )

    return len(records)


def publish_products(accepted_records, run_id):
    """Publish accepted product records with source lineage."""

    if accepted_records.empty:
        return 0

    records = accepted_records.copy()
    records = records.astype(object).where(pd.notna(records), None)

    with engine.begin() as connection:
        for record in records.to_dict(orient="records"):
            connection.execute(
                text("""
                    INSERT INTO ecommerce.products (
                        product_id,
                        product_name,
                        sku,
                        category,
                        price,
                        created_at,
                        source_file,
                        source_record_id,
                        run_id
                    )
                    VALUES (
                        :product_id,
                        :product_name,
                        :sku,
                        :category,
                        :price,
                        :created_at,
                        :source_file,
                        :source_record_id,
                        :run_id
                    )
                    ON CONFLICT (product_id)
                    DO UPDATE SET
                        product_name = EXCLUDED.product_name,
                        sku = EXCLUDED.sku,
                        category = EXCLUDED.category,
                        price = EXCLUDED.price,
                        created_at = EXCLUDED.created_at,
                        source_file = EXCLUDED.source_file,
                        source_record_id = EXCLUDED.source_record_id,
                        run_id = EXCLUDED.run_id,
                        ingested_at = CURRENT_TIMESTAMP
                """),
                {
                    **record,
                    "run_id": run_id,
                },
            )

    return len(records)



def publish_orders(accepted_records, run_id):
    """Publish accepted orders with source lineage."""

    if accepted_records.empty:
        return 0

    records = accepted_records.astype(object).where(
        pd.notna(accepted_records), None
    )

    with engine.begin() as connection:
        for record in records.to_dict(orient="records"):
            connection.execute(
                text("""
                    INSERT INTO ecommerce.orders (
                        order_id, customer_id, order_date, order_status,
                        total_amount, created_at, source_file,
                        source_record_id, run_id
                    )
                    VALUES (
                        :order_id, :customer_id, :order_date, :order_status,
                        :total_amount, :created_at, :source_file,
                        :source_record_id, :run_id
                    )
                    ON CONFLICT (order_id)
                    DO UPDATE SET
                        customer_id = EXCLUDED.customer_id,
                        order_date = EXCLUDED.order_date,
                        order_status = EXCLUDED.order_status,
                        total_amount = EXCLUDED.total_amount,
                        source_file = EXCLUDED.source_file,
                        source_record_id = EXCLUDED.source_record_id,
                        run_id = EXCLUDED.run_id,
                        ingested_at = CURRENT_TIMESTAMP
                """),
                {**record, "run_id": run_id},
            )

    return len(records)


def publish_order_items(accepted_records, run_id):
    """Publish accepted order items with source lineage."""

    if accepted_records.empty:
        return 0

    records = accepted_records.astype(object).where(
        pd.notna(accepted_records), None
    )

    with engine.begin() as connection:
        for record in records.to_dict(orient="records"):
            connection.execute(
                text("""
                    INSERT INTO ecommerce.order_items (
                        order_item_id, order_id, product_id, quantity,
                        unit_price, source_file, source_record_id, run_id
                    )
                    VALUES (
                        :order_item_id, :order_id, :product_id, :quantity,
                        :unit_price, :source_file, :source_record_id, :run_id
                    )
                    ON CONFLICT (order_item_id)
                    DO UPDATE SET
                        order_id = EXCLUDED.order_id,
                        product_id = EXCLUDED.product_id,
                        quantity = EXCLUDED.quantity,
                        unit_price = EXCLUDED.unit_price,
                        source_file = EXCLUDED.source_file,
                        source_record_id = EXCLUDED.source_record_id,
                        run_id = EXCLUDED.run_id,
                        ingested_at = CURRENT_TIMESTAMP
                """),
                {**record, "run_id": run_id},
            )

    return len(records)
