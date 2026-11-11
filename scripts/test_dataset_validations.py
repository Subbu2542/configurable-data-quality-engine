
import pandas as pd

from pipeline.validation.rule_loader import load_validation_rules
from pipeline.validation.engine import run_dataset_validations


# Load actual customer data
df = pd.read_csv("data/input/customers.csv")

# Retrieve rules from PostgreSQL
rules = load_validation_rules("customers")

# Execute configured rules
results = run_dataset_validations(df, rules)

print("Dataset: customers")
print("Total records:", len(df))

for result in results:
    print("\nRule:", result["rule_name"])
    print("Status:", result["status"])
    print("Total:", result["total_records"])
    print("Passed:", result["passed_records"])
    print("Failed:", result["failed_records"])
