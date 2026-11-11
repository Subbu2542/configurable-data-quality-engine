import hashlib
from pathlib import Path

import pandas as pd

from pipeline.validation.rule_loader import load_validation_rules
from pipeline.validation.engine import validate_dataset_records
from backend.services.pipeline_repository import (
    create_pipeline_run,
    save_validation_outputs,
    publish_products,
)

DATASET_NAME = "products"
SOURCE_FILE = Path("data/input/products.csv")

df = pd.read_csv(SOURCE_FILE)

file_fingerprint = hashlib.sha256(SOURCE_FILE.read_bytes()).hexdigest()

rules = load_validation_rules(DATASET_NAME)

result = validate_dataset_records(
    df,
    rules,
    source_file=SOURCE_FILE.name,
)

run = create_pipeline_run(
    dataset_name=DATASET_NAME,
    source_file=SOURCE_FILE.name,
    source_fingerprint=file_fingerprint,
    idempotency_key=file_fingerprint,
)

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
    print("Persistence:", summary)

if run["status"] in ("RUNNING", "SUCCESS", "PARTIAL_SUCCESS"):
    published_count = publish_products(
        accepted_records=result["accepted_records"],
        run_id=run["run_id"],
    )
    print(f"Products published: {published_count}")
else:
    print("Pipeline run cannot be published:", run)