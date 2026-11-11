
import pandas as pd

from pipeline.validation.engine import check_allowed_values

df = pd.DataFrame({
    "order_status": [
        "PLACED",
        "SHIPPED",
        "DELIVERED",
        "INVALID",
        "CANCELLED"
    ]
})

allowed_statuses = [
    "PLACED",
    "PROCESSING",
    "SHIPPED",
    "DELIVERED",
    "CANCELLED"
]

result = check_allowed_values(
    df,
    "order_status",
    allowed_statuses
)

print("Allowed-value validation failures:")
print(result.tolist())
