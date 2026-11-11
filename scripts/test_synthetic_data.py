
from pipeline.synthetic_data import generate_customers

customers = generate_customers(10, seed=42)

print("Generated customer records:")
print(customers)

print("\nTotal customers:", len(customers))
print("Unique customer IDs:", customers["customer_id"].nunique())
print("Unique emails:", customers["email"].nunique())


from pipeline.synthetic_data import generate_products

products = generate_products(20, seed=42)

print("\nGenerated product records:")
print(products.head())

print("\nTotal products:", len(products))
print("Unique product IDs:", products["product_id"].nunique())
print("Unique SKUs:", products["sku"].nunique())
print("Minimum price:", products["price"].min())


from pipeline.synthetic_data import generate_orders

orders = generate_orders(customers, 30, seed=42)

print("\nGenerated order records:")
print(orders.head())

print("\nTotal orders:", len(orders))
print("Unique order IDs:", orders["order_id"].nunique())

print(
    "Valid customer references:",
    orders["customer_id"].isin(
        customers["customer_id"]
    ).all()
)



from pipeline.synthetic_data import generate_order_items

order_items = generate_order_items(
    orders,
    products,
    seed=42
)

print("\nGenerated order items:")
print(order_items.head())

print("\nTotal order items:", len(order_items))

print(
    "Valid order references:",
    order_items["order_id"].isin(
        orders["order_id"]
    ).all()
)

print(
    "Valid product references:",
    order_items["product_id"].isin(
        products["product_id"]
    ).all()
)

print(
    "All quantities positive:",
    (order_items["quantity"] > 0).all()
)


