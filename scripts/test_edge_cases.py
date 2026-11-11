
import json
from pathlib import Path

import pandas as pd

from pipeline.validation.rule_loader import load_validation_rules
from pipeline.validation.engine import validate_dataset_records


SOURCE = Path("data/large_input")
FIXTURES = Path("data/edge_cases")
REPORTS = Path("reports")

REPORTS.mkdir(parents=True, exist_ok=True)

datasets = ["customers", "products", "orders", "order_items"]

analysis = []
total_tests = 0
total_passed = 0


for dataset_name in datasets:
    fixture_file = FIXTURES / f"{dataset_name}.csv"

    df = pd.read_csv(fixture_file)
    manifest = pd.read_csv(
        FIXTURES / "edge_case_manifest.csv"
    )

    manifest = manifest[
        manifest["dataset_name"] == dataset_name
    ]

    rules = load_validation_rules(dataset_name)
    rule_names = {
        str(rule["rule_id"]): rule["rule_name"]
        for rule in rules
    }

    references = {}

    if dataset_name == "orders":
        references["customers"] = pd.read_csv(
            SOURCE / "customers.csv"
        )

    elif dataset_name == "order_items":
        references["orders"] = pd.read_csv(
            SOURCE / "orders.csv"
        )
        references["products"] = pd.read_csv(
            SOURCE / "products.csv"
        )

    result = validate_dataset_records(
        df,
        rules,
        reference_dataframes=references,
        source_file=fixture_file.name,
    )

    rejected_lookup = {
        row["source_record_id"]: row
        for row in result["rejected_records"].to_dict(
            orient="records"
        )
    }

    for _, case in manifest.iterrows():
        fixture_row = int(case["fixture_row"])
        source_record_id = (
            f"{fixture_file.name}:record:{fixture_row}"
        )

        rejected = rejected_lookup.get(source_record_id)

        actual_outcome = "REJECT" if rejected else "ACCEPT"
        expected_outcome = case["expected_outcome"]
        passed = actual_outcome == expected_outcome

        total_tests += 1
        total_passed += int(passed)

        failed_ids = (
            [str(rule_id) for rule_id in
             rejected.get("failed_rule_ids", [])]
            if rejected else []
        )

        failed_names = [
            rule_names.get(rule_id, rule_id)
            for rule_id in failed_ids
        ]

        record = df.iloc[fixture_row - 1].to_dict()
        safe_record = {
            key: (None if pd.isna(value) else value)
            for key, value in record.items()
        }

        analysis.append({
            "dataset_name": dataset_name,
            "fixture_row": fixture_row,
            "scenario": case["scenario"],
            "expected_outcome": expected_outcome,
            "actual_outcome": actual_outcome,
            "test_passed": passed,
            "source_record_id": source_record_id,
            "failed_rule_names": "; ".join(failed_names),
            "rejection_reason": (
                rejected["rejection_reason"] if rejected else ""
            ),
            "record_data": json.dumps(
                safe_record, default=str
            ),
        })


analysis_df = pd.DataFrame(analysis)

detail_path = REPORTS / "edge_case_rejection_analysis.csv"
analysis_df.to_csv(detail_path, index=False)

summary_df = (
    analysis_df[
        analysis_df["actual_outcome"] == "REJECT"
    ]
    .groupby(
        ["dataset_name", "rejection_reason"],
        dropna=False,
    )
    .size()
    .reset_index(name="rejected_records")
)

summary_path = REPORTS / "edge_case_rejection_summary.csv"
summary_df.to_csv(summary_path, index=False)

print("\n========== EDGE CASE ANALYSIS ==========")
print(f"Total scenarios: {total_tests}")
print(f"Passed: {total_passed}")
print(f"Failed: {total_tests - total_passed}")

print("\nRejected record analysis:")
print(summary_df.to_string(index=False))

print(f"\nDetailed report: {detail_path}")
print(f"Rejection summary: {summary_path}")
