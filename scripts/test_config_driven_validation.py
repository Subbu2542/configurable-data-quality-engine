
import pandas as pd

from pipeline.validation.engine import execute_validation_rule


df = pd.DataFrame({
    "price": [100, 200, 0, -10, 500]
})

failed = execute_validation_rule(
    df=df,
    rule_type="RANGE",
    column_name="price",
    parameters={
        "minimum": 0,
        "exclusive_minimum": True
    }
)

print("Total records:", len(df))
print("Passed records:", int((~failed).sum()))
print("Failed records:", int(failed.sum()))
print("Failure details:", failed.tolist())
