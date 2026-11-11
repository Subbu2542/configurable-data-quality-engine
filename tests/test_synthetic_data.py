import pandas as pd
import pytest

from pipeline.synthetic_data import generate_all_data


def test_generation_is_reproducible():
    first = generate_all_data(
        number_of_customers=12,
        number_of_products=6,
        number_of_orders=20,
        seed=42,
    )
    second = generate_all_data(
        number_of_customers=12,
        number_of_products=6,
        number_of_orders=20,
        seed=42,
    )

    for dataset_name in first:
        pd.testing.assert_frame_equal(
            first[dataset_name], second[dataset_name]
        )


def test_generator_creates_requested_dataset_counts():
    data = generate_all_data(
        number_of_customers=12,
        number_of_products=6,
        number_of_orders=20,
        seed=42,
    )

    assert len(data["customers"]) == 12
    assert len(data["products"]) == 6
    assert len(data["orders"]) == 20
    assert len(data["order_items"]) > 0


def test_generated_orders_reference_existing_customers():
    data = generate_all_data(
        number_of_customers=12,
        number_of_products=6,
        number_of_orders=20,
        seed=42,
    )

    customer_ids = set(data["customers"]["customer_id"])
    assert set(data["orders"]["customer_id"]).issubset(customer_ids)


def test_generated_order_items_reference_existing_orders_and_products():
    data = generate_all_data(
        number_of_customers=12,
        number_of_products=6,
        number_of_orders=20,
        seed=42,
    )

    order_ids = set(data["orders"]["order_id"])
    product_ids = set(data["products"]["product_id"])

    assert set(data["order_items"]["order_id"]).issubset(order_ids)
    assert set(data["order_items"]["product_id"]).issubset(product_ids)


def test_order_totals_match_generated_order_items():
    data = generate_all_data(
        number_of_customers=12,
        number_of_products=6,
        number_of_orders=20,
        seed=42,
    )

    items = data["order_items"].copy()
    items["calculated_total"] = items["quantity"] * items["unit_price"]

    expected_totals = items.groupby("order_id")[
        "calculated_total"
    ].sum()

    actual_totals = data["orders"].set_index("order_id")["total_amount"]

    pd.testing.assert_series_equal(
        actual_totals.sort_index(),
        expected_totals.reindex(actual_totals.index).fillna(0).round(2).sort_index(),
        check_names=False,
        check_dtype=False,
    )


def test_generator_rejects_orders_without_customers():
    from pipeline.synthetic_data import generate_orders

    with pytest.raises(ValueError):
        generate_orders(
            pd.DataFrame(columns=["customer_id"]),
            number_of_orders=1,
        )
