
import pandas as pd

from pipeline.validation.rule_loader import load_validation_rules
from pipeline.validation.engine import run_dataset_validations


# Load all four generated datasets
datasets = {
    "customers": pd.read_csv("data/input/customers.csv"),
    "products": pd.read_csv("data/input/products.csv"),
    "orders": pd.read_csv("data/input/orders.csv"),
    "order_items": pd.read_csv("data/input/order_items.csv")
}

# Define parent dataset references
references = {
    "customers": {},
    "products": {},
    "orders": {
        "customers": datasets["customers"]
    },
    "order_items": {
        "orders": datasets["orders"],
        "products": datasets["products"]
    }
}

# Execute rules in dependency order
total_rules = 0
overall_failures = 0

for dataset_name in [
    "customers",
    "products",
    "orders",
    "order_items"
]:

    df = datasets[dataset_name]

    rules = load_validation_rules(dataset_name)

    results = run_dataset_validations(
        df=df,
        rules=rules,
        reference_dataframes=references[dataset_name]
    )

    print(f"\n{'=' * 50}")
    print("DATASET:", dataset_name)
    print("INPUT RECORDS:", len(df))
    print("CONFIGURED RULES:", len(rules))

    for result in results:
        print(
            f"{result['rule_name']}: "
            f"{result['status']} | "
            f"Passed: {result['passed_records']} | "
            f"Failed: {result['failed_records']}"
        )

        total_rules += 1
        overall_failures += result["failed_records"]

print(f"\n{'=' * 50}")
print("TOTAL RULES EXECUTED:", total_rules)
print("TOTAL RULE FAILURES:", overall_failures)
print(
    "OVERALL STATUS:",
    "PASS" if overall_failures == 0 else "FAIL"
)
