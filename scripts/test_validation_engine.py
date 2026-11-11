
import pandas as pd

from pipeline.validation.engine import (
    check_completeness,
    check_uniqueness
)


df = pd.DataFrame({
    "customer_id": [1, 2, 3, 2, 4],
    "customer_name": ["Ravi", None, "Kiran", "", "Arun"],
    "email": [
        "ravi@example.com",
        "kiran@example.com",
        "ravi@example.com",
        "arun@example.com",
        "arun@example.com"
    ]
})

print("Completeness failures:")
print(check_completeness(df, "customer_name").tolist())

print("\nCustomer ID uniqueness failures:")
print(check_uniqueness(df, "customer_id").tolist())

print("\nEmail uniqueness failures:")
print(
    check_uniqueness(
        df,
        "email",
        case_insensitive=True
    ).tolist()
)
