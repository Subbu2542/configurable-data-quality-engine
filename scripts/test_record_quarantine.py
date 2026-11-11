
import pandas as pd

from pipeline.validation.rule_loader import load_validation_rules
from pipeline.validation.engine import validate_dataset_records


# Load customers
df = pd.read_csv("data/input/customers.csv")

# Introduce one invalid record for testing
df.loc[0, "email"] = None

# Load configured rules from PostgreSQL
rules = load_validation_rules("customers")

# Execute validation
output = validate_dataset_records(
    df=df,
    rules=rules,
    source_file="customers.csv"
)

print("Input records:", len(df))
print("Accepted records:", len(output["accepted_records"]))
print("Rejected records:", len(output["rejected_records"]))

print("\nRejected record details:")

print(
    output["rejected_records"][
        [
            "customer_id",
            "email",
            "source_file",
            "source_record_id",
            "rejection_reason"
        ]
    ].to_string(index=False)
)

print("\nValidation rule results:")

for result in output["validation_results"]:
    print(
        result["rule_name"],
        "| Failed:",
        result["failed_records"]
    )
