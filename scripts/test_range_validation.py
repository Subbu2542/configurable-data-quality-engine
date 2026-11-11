import pandas as pd

from pipeline.validation.engine import check_range

df = pd.DataFrame({
    "price": [100, 500, 0, -20, 1000]
})

result = check_range(
    df,
    "price",
    minimum=0,
    exclusive_minimum=True,
    maximum=1000
)

print("Range validation failures:")
print(result.tolist())