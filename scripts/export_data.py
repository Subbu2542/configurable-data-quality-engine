
from pipeline.synthetic_data import (
    generate_all_data,
    save_data_to_csv
)

data = generate_all_data(
    number_of_customers=100,
    number_of_products=50,
    number_of_orders=200,
    seed=42
)

save_data_to_csv(data)

print("\nAll datasets exported successfully.")
