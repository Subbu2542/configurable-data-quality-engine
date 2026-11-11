
import hashlib
from pathlib import Path

import pandas as pd

from pipeline.validation.rule_loader import load_validation_rules
from pipeline.validation.engine import validate_dataset_records
from backend.services.pipeline_repository import (
    create_pipeline_run,
    save_validation_outputs,
    publish_orders,
    publish_order_items,
)

DATASETS = [
    ("orders", "data/input/orders.csv", publish_orders),
    ("order_items", "data/input/order_items.csv", publish_order_items),
]

for dataset_name, file_path, publish_function in DATASETS:
    source_file = Path(file_path)
    df = pd.read_csv(source_file)

    fingerprint = hashlib.sha256(source_file.read_bytes()).hexdigest()
    rules = load_validation_rules(dataset_name)

    references = {}
    if dataset_name == "orders":
        references["customers"] = pd.read_csv("data/input/customers.csv")
    else:
        references["orders"] = pd.read_csv("data/input/orders.csv")
        references["products"] = pd.read_csv("data/input/products.csv")

    result = validate_dataset_records(
        df,
        rules,
        reference_dataframes=references,
        source_file=source_file.name,
    )

    run = create_pipeline_run(
        dataset_name=dataset_name,
        source_file=source_file.name,
        source_fingerprint=fingerprint,
        idempotency_key=fingerprint,
    )

    print(f"\nDataset: {dataset_name}")
    print(f"Run status: {run['status']}")

    if run["status"] == "RUNNING":
        summary = save_validation_outputs(
            run_id=run["run_id"],
            dataset_id=run["dataset_id"],
            dataset_name=dataset_name,
            source_file=source_file.name,
            input_records=len(df),
            validation_results=result["validation_results"],
            rejected_records=result["rejected_records"],
        )
        print("Persistence:", summary)

    if run["status"] in ("RUNNING", "SUCCESS", "PARTIAL_SUCCESS"):
        count = publish_function(
            accepted_records=result["accepted_records"],
            run_id=run["run_id"],
        )
        print(f"Published records: {count}")
    else:
        print("Publishing skipped:", run)
