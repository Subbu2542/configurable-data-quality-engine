
# Database Design

## Database
PostgreSQL

## Logical Schemas

### 1. platform
Responsible for managing the Data Quality Platform.

Tables:
- datasets
- dataset_schemas
- validation_rules
- pipeline_runs
- validation_results
- quarantine_records
- pipeline_logs

### 2. ecommerce
Stores the business datasets.

Tables:
- customers
- products
- orders
- order_items

## Relationships

- One dataset has many schema definitions.
- One dataset has many validation rules.
- One dataset has many pipeline runs.
- One pipeline run produces many validation results.
- One validation rule can be evaluated in many runs.
- One pipeline run can generate many quarantine records.
- One pipeline run can generate many logs.

## Primary Key Strategy

- Platform entities use UUID identifiers.
- Business entities use stable source business identifiers.
- Run IDs are generated uniquely for every execution.

## Data Types

- IDs: UUID or BIGINT
- Names: VARCHAR
- Amounts: NUMERIC
- Quantities: INTEGER
- Timestamps: TIMESTAMPTZ
- Rule parameters and source records: JSONB
- Status fields: VARCHAR with database constraints

## Reliability

- Enforce primary and foreign key constraints.
- Use unique constraints for business keys.
- Use database transactions for publishing.
- Maintain rejected records separately.
- Preserve execution history.
- Support safe reruns through deterministic keys and conflict handling.

## Naming Conventions

- snake_case table and column names.
- UTC timestamps.
- Explicit run_id and source_file metadata.
- ISO-8601 timestamp representation.
