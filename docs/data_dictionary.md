
# Data Dictionary

## Project
Configurable Data Quality and Engineering Platform

## Business Domain
E-commerce

## Source Datasets

### 1. customers
Grain: One record per customer.

- customer_id: Unique customer identifier (Primary Key)
- customer_name: Customer full name (Required)
- email: Customer email (Required)
- phone: Customer phone number (Optional)
- city: Customer city (Optional)
- created_at: Record creation timestamp
- updated_at: Last modification timestamp

### 2. products
Grain: One record per product.

- product_id: Unique product identifier (Primary Key)
- product_name: Product name (Required)
- sku: Unique stock keeping unit
- category: Product category
- price: Product selling price (Must be positive)
- created_at: Product creation timestamp

### 3. orders
Grain: One record per order.

- order_id: Unique order identifier (Primary Key)
- customer_id: Customer reference (Foreign Key)
- order_date: Order creation timestamp
- order_status: Order status
- total_amount: Order total (Must be non-negative)
- created_at: Record creation timestamp

### 4. order_items
Grain: One record per product within an order.

- order_item_id: Unique order item identifier (Primary Key)
- order_id: Order reference (Foreign Key)
- product_id: Product reference (Foreign Key)
- quantity: Number of purchased units (Must be positive)
- unit_price: Price per unit
- line_total: Derived as quantity * unit_price

## Relationships

- customers (1) -> orders (N)
- orders (1) -> order_items (N)
- products (1) -> order_items (N)

## Naming Conventions

- Table names use snake_case.
- Column names use snake_case.
- Timestamps use ISO-8601 representation.
- Primary keys use stable business identifiers.
- Pipeline executions use run_id.
- Source records retain source_file and source identifiers.

## Data Quality Assumptions

- Customer IDs must be unique.
- Product IDs must be unique.
- Product SKUs must be unique.
- Order customer references must exist.
- Order item order references must exist.
- Order item product references must exist.
- Prices and quantities must satisfy their defined business limits.
- Required fields must not be NULL.
- Order statuses must belong to the configured allowed values.

## Traceability

Rejected records must preserve their original source
information, run_id, source_file, source record identifier,
validation rule and rejection reason.

## Historical Data

Changes to business records must not silently destroy
historical information when history is required.
