import hashlib
from pathlib import Path

import pandas as pd

from pipeline.validation.rule_loader import load_validation_rules
from pipeline.validation.engine import validate_dataset_records
from backend.services.pipeline_repository import (
    create_pipeline_run,
    save_validation_outputs,
)

from backend.services.pipeline_repository import (
    create_pipeline_run,
    save_validation_outputs,
    publish_customers,
    publish_products,
)

DATASET_NAME = "customers"
SOURCE_FILE = Path("data/input/customers.csv")

df = pd.read_csv(SOURCE_FILE)

# Introduce one invalid record to test quarantine persistence.
df.loc[0, "email"] = None

file_fingerprint = hashlib.sha256(SOURCE_FILE.read_bytes()).hexdigest()

rules = load_validation_rules(DATASET_NAME)

result = validate_dataset_records(
    df,
    rules,
    source_file=SOURCE_FILE.name,
)
print("Accepted type:", type(result["accepted_records"]))
print("Rejected type:", type(result["rejected_records"]))
print("Rejected preview:")
print(result["rejected_records"])
print("Validation result keys:", result["validation_results"][0].keys())
print("First validation result:", result["validation_results"][0])
print("First database rule:", rules[0])

run = create_pipeline_run(
    dataset_name=DATASET_NAME,
    source_file=SOURCE_FILE.name,
    source_fingerprint=file_fingerprint,
    idempotency_key=file_fingerprint,
)

if run["status"] in ("RUNNING", "SUCCESS", "PARTIAL_SUCCESS"):

    if run["status"] == "RUNNING":
        summary = save_validation_outputs(
            run_id=run["run_id"],
            dataset_id=run["dataset_id"],
            dataset_name=DATASET_NAME,
            source_file=SOURCE_FILE.name,
            input_records=len(df),
            validation_results=result["validation_results"],
            rejected_records=result["rejected_records"],
        )
        print("Persistence test completed:")
        print(summary)

    published_count = publish_customers(
        accepted_records=result["accepted_records"],
        run_id=run["run_id"],
    )

    print(f"Customers published: {published_count}")

else:
    print("Pipeline run is not ready for publishing:")
    print(run)