
from pipeline.synthetic_data import generate_all_data

data = generate_all_data(
    number_of_customers=100,
    number_of_products=50,
    number_of_orders=200,
    seed=42
)

for dataset_name, dataframe in data.items():
    print(f"{dataset_name}: {len(dataframe)} records")

print("\nAll datasets generated successfully.")
