
import json
from pathlib import Path

import pandas as pd

from pipeline.validation.rule_loader import load_validation_rules
from pipeline.validation.engine import validate_dataset_records


INPUT = Path("data/large_input")
PROCESSED = Path("data/processed/large_input")
QUARANTINE = Path("data/quarantine/large_input")
REPORTS = Path("reports")

for folder in (PROCESSED, QUARANTINE, REPORTS):
    folder.mkdir(parents=True, exist_ok=True)

datasets = {
    name: pd.read_csv(INPUT / f"{name}.csv")
    for name in ("customers", "products", "orders", "order_items")
}

reference_data = {
    "customers": datasets["customers"],
    "products": datasets["products"],
    "orders": datasets["orders"],
}

summary = {
    "input_directory": str(INPUT),
    "datasets": {},
    "total_input": 0,
    "total_accepted": 0,
    "total_rejected": 0,
    "order_total_reconciliation": {},
}

validation_results_by_dataset = {}

for dataset_name, df in datasets.items():
    references = {}

    if dataset_name == "orders":
        references["customers"] = reference_data["customers"]

    elif dataset_name == "order_items":
        references["orders"] = reference_data["orders"]
        references["products"] = reference_data["products"]

    rules = load_validation_rules(dataset_name)

    result = validate_dataset_records(
        df,
        rules,
        reference_dataframes=references,
        source_file=f"{dataset_name}.csv",
    )

    accepted = result["accepted_records"]
    rejected = result["rejected_records"]

    accepted_path = PROCESSED / f"{dataset_name}_accepted.csv"
    rejected_path = QUARANTINE / f"{dataset_name}_rejected.csv"

    accepted.to_csv(accepted_path, index=False)
    rejected.to_csv(rejected_path, index=False)

    rule_results = result["validation_results"]

    summary["datasets"][dataset_name] = {
        "input_records": len(df),
        "accepted_records": len(accepted),
        "rejected_records": len(rejected),
        "reconciliation_passed": (
            len(accepted) + len(rejected) == len(df)
        ),
        "rules_executed": len(rule_results),
        "rule_failures": sum(
            item["failed_records"] > 0
            for item in rule_results
        ),
        "validation_results": rule_results,
        "accepted_file": str(accepted_path),
        "rejected_file": str(rejected_path),
    }

    summary["total_input"] += len(df)
    summary["total_accepted"] += len(accepted)
    summary["total_rejected"] += len(rejected)

    validation_results_by_dataset[dataset_name] = rule_results

    print(f"\nDataset: {dataset_name}")
    print(f"Input: {len(df):,}")
    print(f"Accepted: {len(accepted):,}")
    print(f"Rejected: {len(rejected):,}")
    print(f"Rules executed: {len(rule_results)}")


# Reconcile order totals against order item line totals.
orders = datasets["orders"].copy()
items = datasets["order_items"].copy()

items["calculated_line_total"] = (
    items["quantity"] * items["unit_price"]
)

calculated_totals = (
    items.groupby("order_id")["calculated_line_total"]
    .sum()
    .round(2)
)

expected_totals = (
    orders.set_index("order_id")["total_amount"]
    .round(2)
)

comparison = pd.concat(
    [
        expected_totals.rename("order_total"),
        calculated_totals.rename("calculated_total"),
    ],
    axis=1,
)

comparison["difference"] = (
    comparison["order_total"] - comparison["calculated_total"]
).round(2)

comparison["reconciled"] = comparison["difference"].abs() < 0.01

comparison.to_csv(
    REPORTS / "large_order_total_reconciliation.csv"
)

summary["order_total_reconciliation"] = {
    "orders_checked": len(comparison),
    "orders_reconciled": int(comparison["reconciled"].sum()),
    "orders_mismatched": int((~comparison["reconciled"]).sum()),
    "maximum_absolute_difference": float(
        comparison["difference"].abs().max()
    ),
    "report_file": str(
        REPORTS / "large_order_total_reconciliation.csv"
    ),
}

summary["overall_reconciliation_passed"] = (
    summary["total_input"]
    == summary["total_accepted"] + summary["total_rejected"]
)

summary["generated_output_records"] = (
    summary["total_accepted"] + summary["total_rejected"]
)

report_path = REPORTS / "large_validation_report.json"

with report_path.open("w", encoding="utf-8") as file:
    json.dump(summary, file, indent=4, default=str)

print("\n========== LARGE DATA VALIDATION SUMMARY ==========")
print(f"Total input: {summary['total_input']:,}")
print(f"Total accepted: {summary['total_accepted']:,}")
print(f"Total rejected: {summary['total_rejected']:,}")
print(
    "Input/output reconciliation:",
    summary["overall_reconciliation_passed"],
)
print(
    "Order totals reconciled:",
    summary["order_total_reconciliation"]["orders_reconciled"],
    "/",
    summary["order_total_reconciliation"]["orders_checked"],
)
print(f"Report: {report_path}")
