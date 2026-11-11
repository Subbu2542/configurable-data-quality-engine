
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd


# Fixed reference time ensures identical timestamps for identical inputs.
BASE_TIME = datetime(2026, 1, 1, tzinfo=timezone.utc)


def generate_customers(number_of_customers=100, seed=42):
    rng = random.Random(seed)

    first_names = [
        "Ravi", "Priya", "Kiran", "Arjun", "Sneha",
        "Rahul", "Divya", "Anil", "Meera", "Vijay",
    ]

    last_names = [
        "Kumar", "Reddy", "Sharma", "Patel", "Rao",
        "Verma", "Gupta", "Naidu", "Singh", "Das",
    ]

    cities = [
        "Hyderabad", "Bengaluru", "Chennai",
        "Vijayawada", "Visakhapatnam", "Mumbai",
    ]

    customers = []

    for customer_id in range(1, number_of_customers + 1):
        first_name = rng.choice(first_names)
        last_name = rng.choice(last_names)

        created_at = BASE_TIME - timedelta(
            days=rng.randint(1, 1000)
        )

        customers.append({
            "customer_id": customer_id,
            "customer_name": f"{first_name} {last_name}",
            "email": (
                f"{first_name.lower()}.{last_name.lower()}"
                f"{customer_id}@example.com"
            ),
            "phone": f"9{rng.randint(100000000, 999999999)}",
            "city": rng.choice(cities),
            "created_at": created_at,
            "updated_at": created_at + timedelta(
                days=rng.randint(0, 30)
            ),
        })

    return pd.DataFrame(customers)


def generate_products(number_of_products=50, seed=42):
    rng = random.Random(seed + 1)

    product_names = [
        "Laptop", "Smartphone", "Headphones",
        "Keyboard", "Mouse", "Monitor",
        "Tablet", "Smartwatch", "Speaker",
        "Power Bank",
    ]

    categories = [
        "Electronics", "Accessories",
        "Computers", "Mobile Devices",
    ]

    products = []

    for product_id in range(1, number_of_products + 1):
        products.append({
            "product_id": product_id,
            "product_name": rng.choice(product_names),
            "sku": f"SKU-{product_id:05d}",
            "category": rng.choice(categories),
            "price": round(rng.uniform(100, 100000), 2),
            "created_at": BASE_TIME - timedelta(
                days=rng.randint(1, 500)
            ),
        })

    return pd.DataFrame(products)


def generate_orders(customers, number_of_orders=100, seed=42):
    if customers.empty and number_of_orders > 0:
        raise ValueError("At least one customer is required.")

    rng = random.Random(seed + 2)

    statuses = [
        "PLACED", "PROCESSING", "SHIPPED",
        "DELIVERED", "CANCELLED",
    ]

    customer_ids = customers["customer_id"].tolist()
    orders = []

    for order_id in range(1, number_of_orders + 1):
        order_date = BASE_TIME - timedelta(
            days=rng.randint(1, 365)
        )

        orders.append({
            "order_id": order_id,
            "customer_id": rng.choice(customer_ids),
            "order_date": order_date,
            "order_status": rng.choice(statuses),
            "total_amount": 0.00,
            "created_at": order_date + timedelta(
                minutes=rng.randint(1, 120)
            ),
        })

    return pd.DataFrame(orders)


def generate_order_items(
    orders,
    products,
    seed=42,
    min_items=1,
    max_items=4,
):
    if min_items < 1 or max_items < min_items:
        raise ValueError("Invalid order item count limits.")

    if products.empty and not orders.empty:
        raise ValueError("At least one product is required.")

    rng = random.Random(seed + 3)

    # Build a lookup once instead of repeatedly searching the DataFrame.
    product_lookup = products.set_index("product_id")["price"].to_dict()
    product_ids = list(product_lookup)

    order_items = []
    order_item_id = 1

    for (order_id,) in orders[["order_id"]].itertuples(
        index=False, name=None
    ):
        number_of_items = rng.randint(min_items, max_items)

        selected_products = rng.sample(
            product_ids,
            k=min(number_of_items, len(product_ids)),
        )

        for product_id in selected_products:
            order_items.append({
                "order_item_id": order_item_id,
                "order_id": order_id,
                "product_id": product_id,
                "quantity": rng.randint(1, 5),
                "unit_price": product_lookup[product_id],
            })

            order_item_id += 1

    return pd.DataFrame(
        order_items,
        columns=[
            "order_item_id",
            "order_id",
            "product_id",
            "quantity",
            "unit_price",
        ],
    )


def generate_all_data(
    number_of_customers=100,
    number_of_products=50,
    number_of_orders=200,
    seed=42,
):
    customers = generate_customers(number_of_customers, seed)
    products = generate_products(number_of_products, seed)

    orders = generate_orders(
        customers,
        number_of_orders,
        seed,
    )

    order_items = generate_order_items(
        orders,
        products,
        seed,
    )

    if not order_items.empty:
        order_items["line_total"] = (
            order_items["quantity"] * order_items["unit_price"]
        )

        order_totals = order_items.groupby(
            "order_id"
        )["line_total"].sum()

        orders["total_amount"] = (
            orders["order_id"].map(order_totals).fillna(0).round(2)
        )

        order_items = order_items.drop(columns=["line_total"])

    return {
        "customers": customers,
        "products": products,
        "orders": orders,
        "order_items": order_items,
    }


def save_data_to_csv(data, output_directory="data/input"):
    output_path = Path(output_directory)
    output_path.mkdir(parents=True, exist_ok=True)

    for dataset_name, dataframe in data.items():
        file_path = output_path / f"{dataset_name}.csv"
        dataframe.to_csv(file_path, index=False)

        print(
            f"Saved {dataset_name}: "
            f"{len(dataframe):,} records -> {file_path}"
        )
