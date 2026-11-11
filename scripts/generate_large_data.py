
import argparse

from pipeline.synthetic_data import (
    generate_all_data,
    save_data_to_csv,
)


def main():
    parser = argparse.ArgumentParser(
        description="Generate scalable synthetic e-commerce datasets."
    )

    parser.add_argument("--customers", type=int, default=10000)
    parser.add_argument("--products", type=int, default=5000)
    parser.add_argument("--orders", type=int, default=50000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--output",
        default="data/large_input",
    )

    args = parser.parse_args()

    if min(args.customers, args.products, args.orders) < 1:
        parser.error("All dataset sizes must be greater than zero.")

    data = generate_all_data(
        number_of_customers=args.customers,
        number_of_products=args.products,
        number_of_orders=args.orders,
        seed=args.seed,
    )

    total_records = sum(len(df) for df in data.values())

    print("\nGenerated dataset summary:")

    for name, dataframe in data.items():
        print(f"{name}: {len(dataframe):,}")

    print(f"TOTAL RECORDS: {total_records:,}")

    if total_records < 100000:
        raise RuntimeError(
            "Generated volume is below the 100,000-record target."
        )

    save_data_to_csv(data, args.output)


if __name__ == "__main__":
    main()
