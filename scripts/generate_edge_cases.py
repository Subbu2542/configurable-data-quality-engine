
from pathlib import Path

import pandas as pd


SOURCE = Path("data/large_input")
OUTPUT = Path("data/edge_cases")

datasets = {
    "customers": [],
    "products": [],
    "orders": [],
    "order_items": [],
}

manifest = []


def sample(dataset, index):
    return pd.read_csv(SOURCE / f"{dataset}.csv").iloc[index].to_dict()


def add_case(dataset, record, scenario, expected, description):
    datasets[dataset].append(record.copy())

    manifest.append({
        "dataset_name": dataset,
        "fixture_row": len(datasets[dataset]),
        "scenario": scenario,
        "expected_outcome": expected,
        "description": description,
    })


# -------------------------------------------------
# CUSTOMERS
# -------------------------------------------------

c0 = sample("customers", 0)
c1 = sample("customers", 1)
c2 = sample("customers", 2)

normal_customer = c0.copy()
normal_customer["customer_id"] = 900001
normal_customer["email"] = "normal.edge.customer@example.com"

add_case(
    "customers", normal_customer,
    "normal_customer", "ACCEPT",
    "Normal customer record",
)

# Both occurrences are expected to fail uniqueness validation.
duplicate_customer = c0.copy()
add_case(
    "customers", duplicate_customer,
    "duplicate_customer_id_original", "REJECT",
    "First occurrence of duplicated customer ID",
)
add_case(
    "customers", duplicate_customer,
    "duplicate_customer_id_copy", "REJECT",
    "Duplicate customer ID record",
)

missing_email = c1.copy()
missing_email["email"] = None
add_case(
    "customers", missing_email,
    "missing_email", "REJECT",
    "Mandatory email is missing",
)

missing_name = c2.copy()
missing_name["customer_name"] = None
add_case(
    "customers", missing_name,
    "missing_customer_name", "REJECT",
    "Mandatory customer name is missing",
)


# -------------------------------------------------
# PRODUCTS
# -------------------------------------------------

p0 = sample("products", 0)
p1 = sample("products", 1)
p2 = sample("products", 2)
p3 = sample("products", 3)

add_case(
    "products", p0,
    "normal_product", "ACCEPT",
    "Normal product record",
)

minimum_price = p0.copy()
minimum_price["product_id"] = 900001
minimum_price["sku"] = "EDGE-MIN-PRICE"
minimum_price["price"] = 0.01

add_case(
    "products", minimum_price,
    "minimum_positive_price", "ACCEPT",
    "Minimum positive price boundary",
)

maximum_price = p1.copy()
maximum_price["product_id"] = 900002
maximum_price["sku"] = "EDGE-MAX-PRICE"
maximum_price["price"] = 100000.00

add_case(
    "products", maximum_price,
    "maximum_generated_price", "ACCEPT",
    "Upper boundary of the generator price range",
)

# Duplicate SKU with distinct product IDs.
duplicate_sku_a = p1.copy()
duplicate_sku_b = p1.copy()

duplicate_sku_a["product_id"] = 900003
duplicate_sku_b["product_id"] = 900004
duplicate_sku_a["sku"] = "EDGE-DUPLICATE-SKU"
duplicate_sku_b["sku"] = "EDGE-DUPLICATE-SKU"

add_case(
    "products", duplicate_sku_a,
    "duplicate_sku_original", "REJECT",
    "First occurrence of duplicated SKU",
)
add_case(
    "products", duplicate_sku_b,
    "duplicate_sku_copy", "REJECT",
    "Second occurrence of duplicated SKU",
)

missing_product_name = p2.copy()
missing_product_name["product_id"] = 900005
missing_product_name["sku"] = "EDGE-MISSING-NAME"
missing_product_name["product_name"] = None

add_case(
    "products", missing_product_name,
    "missing_product_name", "REJECT",
    "Mandatory product name is missing",
)

negative_price = p3.copy()
negative_price["product_id"] = 900006
negative_price["sku"] = "EDGE-NEGATIVE-PRICE"
negative_price["price"] = -0.01

add_case(
    "products", negative_price,
    "negative_price", "REJECT",
    "Product price is below the permitted range",
)


# -------------------------------------------------
# ORDERS
# -------------------------------------------------

order_samples = [sample("orders", i) for i in range(8)]
max_order_id = int(
    pd.read_csv(SOURCE / "orders.csv")["order_id"].max()
)

add_case(
    "orders", order_samples[0],
    "normal_order", "ACCEPT",
    "Normal order with an existing customer reference",
)

# Duplicate order ID pair.
duplicate_order = order_samples[1].copy()
duplicate_order["order_id"] = max_order_id + 101

add_case(
    "orders", duplicate_order,
    "duplicate_order_id_original", "REJECT",
    "First occurrence of duplicated order ID",
)
add_case(
    "orders", duplicate_order,
    "duplicate_order_id_copy", "REJECT",
    "Duplicate order ID record",
)

missing_customer = order_samples[2].copy()
missing_customer["order_id"] = max_order_id + 102
missing_customer["customer_id"] = None

add_case(
    "orders", missing_customer,
    "missing_customer_reference", "REJECT",
    "Customer reference is missing",
)

invalid_customer = order_samples[3].copy()
invalid_customer["order_id"] = max_order_id + 103
invalid_customer["customer_id"] = 999999999

add_case(
    "orders", invalid_customer,
    "invalid_customer_reference", "REJECT",
    "Customer ID does not exist",
)

invalid_status = order_samples[4].copy()
invalid_status["order_id"] = max_order_id + 104
invalid_status["order_status"] = "UNKNOWN"

add_case(
    "orders", invalid_status,
    "invalid_order_status", "REJECT",
    "Order status is not an allowed value",
)

negative_total = order_samples[5].copy()
negative_total["order_id"] = max_order_id + 105
negative_total["total_amount"] = -0.01

add_case(
    "orders", negative_total,
    "negative_order_total", "REJECT",
    "Order total is negative",
)

zero_total = order_samples[6].copy()
zero_total["order_id"] = max_order_id + 106
zero_total["total_amount"] = 0.00

add_case(
    "orders", zero_total,
    "zero_order_total_boundary", "ACCEPT",
    "Zero total boundary for range validation",
)

# Newer event first, older event appended later.
newer_order = order_samples[6].copy()
newer_order["order_id"] = max_order_id + 107
newer_order["order_date"] = "2025-12-31T00:00:00+00:00"
newer_order["created_at"] = "2026-01-01T00:00:00+00:00"

add_case(
    "orders", newer_order,
    "newer_order_event", "ACCEPT",
    "Newer business event arrives first",
)

late_order = order_samples[7].copy()
late_order["order_id"] = max_order_id + 108
late_order["order_date"] = "2024-01-01T00:00:00+00:00"
late_order["created_at"] = "2026-01-01T00:00:00+00:00"

add_case(
    "orders", late_order,
    "late_arriving_out_of_order_order", "ACCEPT",
    "Older business event arrives after a newer event",
)


# -------------------------------------------------
# ORDER ITEMS
# -------------------------------------------------

item_samples = [sample("order_items", i) for i in range(5)]
max_item_id = int(
    pd.read_csv(SOURCE / "order_items.csv")[
        "order_item_id"
    ].max()
)

add_case(
    "order_items", item_samples[0],
    "normal_order_item", "ACCEPT",
    "Normal item with valid order and product references",
)

minimum_quantity = item_samples[1].copy()
minimum_quantity["order_item_id"] = max_item_id + 101
minimum_quantity["quantity"] = 1
minimum_quantity["unit_price"] = 0.01

add_case(
    "order_items", minimum_quantity,
    "minimum_quantity_boundary", "ACCEPT",
    "Minimum permitted positive quantity",
)

duplicate_item = item_samples[2].copy()
duplicate_item["order_item_id"] = max_item_id + 102

add_case(
    "order_items", duplicate_item,
    "duplicate_item_id_original", "REJECT",
    "First occurrence of duplicated item ID",
)
add_case(
    "order_items", duplicate_item,
    "duplicate_item_id_copy", "REJECT",
    "Duplicate order item ID",
)

missing_quantity = item_samples[3].copy()
missing_quantity["order_item_id"] = max_item_id + 103
missing_quantity["quantity"] = None

add_case(
    "order_items", missing_quantity,
    "missing_quantity", "REJECT",
    "Quantity is missing",
)

zero_quantity = item_samples[4].copy()
zero_quantity["order_item_id"] = max_item_id + 104
zero_quantity["quantity"] = 0

add_case(
    "order_items", zero_quantity,
    "zero_quantity", "REJECT",
    "Quantity is below the permitted minimum",
)

invalid_order = item_samples[0].copy()
invalid_order["order_item_id"] = max_item_id + 105
invalid_order["order_id"] = 999999999

add_case(
    "order_items", invalid_order,
    "invalid_order_reference", "REJECT",
    "Referenced order does not exist",
)

invalid_product = item_samples[1].copy()
invalid_product["order_item_id"] = max_item_id + 106
invalid_product["product_id"] = 999999999

add_case(
    "order_items", invalid_product,
    "invalid_product_reference", "REJECT",
    "Referenced product does not exist",
)


# -------------------------------------------------
# SAVE FIXTURES AND LABEL MANIFEST
# -------------------------------------------------

OUTPUT.mkdir(parents=True, exist_ok=True)

for dataset_name, records in datasets.items():
    source_columns = pd.read_csv(
        SOURCE / f"{dataset_name}.csv",
        nrows=0,
    ).columns.tolist()

    dataframe = pd.DataFrame(records, columns=source_columns)

    dataframe.to_csv(
        OUTPUT / f"{dataset_name}.csv",
        index=False,
    )

    print(f"{dataset_name}: {len(dataframe)} edge-case records")

manifest_df = pd.DataFrame(manifest)
manifest_df.to_csv(
    OUTPUT / "edge_case_manifest.csv",
    index=False,
)

print("\nEdge-case generation completed.")
print(f"Total fixture records: {sum(map(len, datasets.values()))}")
print(f"Manifest entries: {len(manifest_df)}")
print(f"Output directory: {OUTPUT}")
print("\nExpected outcomes:")
print(manifest_df["expected_outcome"].value_counts().to_dict())
