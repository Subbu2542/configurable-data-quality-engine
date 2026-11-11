
from pipeline.validation.rule_loader import load_validation_rules


dataset_name = "customers"

rules = load_validation_rules(dataset_name)

print("Dataset:", dataset_name)
print("Total active rules:", len(rules))

for rule in rules:
    print("\nRule:", rule["rule_name"])
    print("Type:", rule["rule_type"])
    print("Column:", rule["column_name"])
    print("Parameters:", rule["parameters"])
    print("Severity:", rule["severity"])
