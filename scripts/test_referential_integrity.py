
import pandas as pd

from pipeline.validation.engine import check_referential_integrity


customers = pd.DataFrame({
    "customer_id": [1, 2, 3, 4]
})

orders = pd.DataFrame({
    "order_id": [101, 102, 103, 104],
    "customer_id": [1, 5, 3, 8]
})

result = check_referential_integrity(
    source_df=orders,
    source_column="customer_id",
    reference_df=customers,
    reference_column="customer_id"
)

print("Referential integrity failures:")
print(result.tolist())