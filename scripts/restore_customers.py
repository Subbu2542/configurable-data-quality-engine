import pandas as pd

from sqlalchemy import text
from backend.services.database import engine

df = pd.read_csv("data/input/customers.csv")

with engine.begin() as connection:
    for index, row in df.iterrows():
        if pd.isna(row["email"]):
            continue

        connection.execute(
            text("""
                INSERT INTO ecommerce.customers (
                    customer_id,
                    customer_name,
                    email,
                    phone,
                    city,
                    created_at,
                    updated_at,
                    source_file,
                    source_record_id
                )
                VALUES (
                    :customer_id,
                    :customer_name,
                    :email,
                    :phone,
                    :city,
                    :created_at,
                    :updated_at,
                    :source_file,
                    :source_record_id
                )
                ON CONFLICT (customer_id)
                DO UPDATE SET
                    email = EXCLUDED.email,
                    customer_name = EXCLUDED.customer_name,
                    phone = EXCLUDED.phone,
                    city = EXCLUDED.city
            """),
            {
                **row.to_dict(),
                "source_file": "customers.csv",
                "source_record_id": f"customers.csv:record:{index + 1}",
            },
        )

print("Customer records restored:", len(df))