# Configurable Data Quality & Engineering Platform

A configurable, rule-driven data engineering platform for validating structured datasets, identifying data quality issues, managing rejected records, and monitoring pipeline execution through an interactive dashboard.

The platform demonstrates a reusable data quality workflow using an e-commerce domain with four datasets: customers, products, orders, and order items.

---

## Project Overview

Data quality is essential for reliable data engineering pipelines. Invalid, incomplete, duplicated, or inconsistent records can affect downstream analytics and business decisions.

This platform provides a centralized solution to:

- Ingest structured CSV datasets.
- Apply configurable data validation rules.
- Separate valid and invalid records.
- Identify and explain validation failures.
- Store accepted records and quarantine rejected records.
- Maintain pipeline execution history and metadata.
- Analyze data quality through an interactive dashboard.
- Validate large datasets and reconcile record counts.

The architecture is designed to be reusable across different structured-data domains by configuring datasets, schemas, and validation rules.

## Key Features

### 1. Configuration-Driven Validation

Supports multiple validation rule types:

- **Completeness:** Identifies missing and empty values.
- **Uniqueness:** Detects duplicate records or field values.
- **Range:** Checks numeric values against configured boundaries.
- **Referential Integrity:** Validates relationships between datasets.
- **Allowed Values:** Checks whether values belong to an approved list.

Validation rules are maintained in PostgreSQL and loaded by the validation engine.

### 2. Accepted and Rejected Record Management

Records are separated according to validation results.

- Accepted records continue through the publishing process.
- Rejected records are sent to quarantine.
- Failed rule IDs and rejection reasons are retained.
- Source filenames and record identifiers support traceability.

ERROR-level validation failures cause rejection. WARNING-level failures are recorded without rejecting the record.

### 3. Pipeline Execution Management

- Pipeline run metadata and status tracking.
- Input, accepted, rejected, and error counts.
- Source file and source fingerprint tracking.
- Idempotent execution support.
- Pipeline execution logs.

### 4. PostgreSQL Persistence

Stores business records and data quality metadata.

### 5. Interactive Analytics Dashboard

The Streamlit dashboard provides:

- Dataset-level record counts.
- Pipeline run history.
- Validation results.
- Quarantined record inspection.
- Edge-case test outcomes.
- Rejection reason analysis.
- Large-volume validation and reconciliation results.

### 6. Synthetic Data Generation

Generates reproducible datasets using configurable record counts and random seeds.

### 7. Large-Volume Validation

Supports a separate large-volume validation workflow with accepted and rejected output files, record reconciliation, and order-total reconciliation.

---

## Architecture

```text
                 CSV / Synthetic Data
                         |
                         v
                   Data Ingestion
                         |
                         v
                Schema & Data Checks
                         |
                         v
                 Validation Engine
                         |
                  +------+------+
                  |             |
                  v             v
            Accepted Data   Rejected Data
                  |             |
                  v             v
             Transformation  Quarantine
                  |             |
                  v             v
              Publishing   Rejection Analysis
                  |
                  v
               PostgreSQL
                  |
                  v
                FastAPI
                  |
                  v
          Streamlit Dashboard
```

## Technology Stack

| Component | Technology |
|---|---|
| Programming Language | Python |
| Data Processing | Pandas |
| Database | PostgreSQL 18 |
| Database Connectivity | SQLAlchemy, psycopg2 |
| Backend API | FastAPI |
| Frontend Dashboard | Streamlit |
| Testing Framework | Pytest |
| API Testing | HTTPX |
| Configuration | JSON, environment variables |
| Version Control | Git |

---

## Project Structure

```text
configurable-data-quality-engine/
│
├── backend/
│   ├── api/
│   ├── schemas/
│   └── services/
│
├── config/
│   ├── rules/
│   └── schemas/
│
├── database/
│   └── migrations/
│       └── schema.sql
│
├── data/
│   ├── input/
│   ├── edge_cases/
│   ├── large_input/
│   ├── processed/
│   └── quarantine/
│
├── docs/
│
├── frontend/
│   ├── pages/
│   └── services/
│
├── pipeline/
│   ├── ingestion/
│   ├── validation/
│   ├── transformation/
│   ├── publishing/
│   ├── quarantine/
│   └── monitoring/
│
├── reports/
│
├── scripts/
│
├── tests/
│   ├── test_validation_engine.py
│   └── test_synthetic_data.py
│
├── .gitignore
├── pytest.ini
├── requirements.txt
└── README.md
```

---

## Installation and Setup

### Prerequisites

- Python 3.13 or later.
- PostgreSQL 18 or a compatible PostgreSQL version.
- Git.
- VS Code or another Python editor.
- Windows PowerShell or an equivalent terminal.

### 1. Clone the Repository

```powershell
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd configurable-data-quality-engine
```

### 2. Create a Virtual Environment

```powershell
py -3.13 -m venv .venv
```

Activate it:

```powershell
.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

---

## Database Configuration

### 1. Create the PostgreSQL Database

Create a database named:

```sql
CREATE DATABASE data_quality_platform;
```

### 2. Apply the Database Schema

Run the schema migration:

```powershell
psql -U postgres -d data_quality_platform -f database/migrations/schema.sql
```

The application uses PostgreSQL for business data, validation rules, pipeline runs, validation results, quarantine records, and pipeline logs.

Ensure the configured datasets and active validation rules are available in the database before executing the pipeline.

### 3. Configure Environment Variables

Create a `.env` file in the project root:

```env
PG_USER=postgres
PG_PASSWORD=your_password
PG_HOST=localhost
PG_PORT=5432
PG_DATABASE=data_quality_platform
```

Replace the example credentials with your local PostgreSQL configuration.

The application loads these variables using `python-dotenv`.

**Security:** Never commit `.env`, database passwords, or other credentials to GitHub.

---

## Running the Application

The application has two main components: FastAPI and Streamlit.

### 1. Start the FastAPI Backend

Open the first terminal:

```powershell
python -m uvicorn backend.api.main:app --reload
```

Backend URL:

`http://127.0.0.1:8000`

Interactive API documentation:

`http://127.0.0.1:8000/docs`

### 2. Start the Streamlit Dashboard

Open a second terminal and activate the virtual environment.

Run:

```powershell
python -m streamlit run frontend/app.py
```

Dashboard URL:

`http://localhost:8501`

Keep both terminals running while using the dashboard.

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Checks API and database health |
| GET | `/dashboard/summary` | Returns dataset and pipeline summary |
| GET | `/runs` | Retrieves pipeline run history |
| GET | `/runs/{run_id}/validations` | Retrieves validation results for a run |
| GET | `/runs/{run_id}/quarantine` | Retrieves quarantined records |
| GET | `/analytics/edge-cases` | Returns edge-case outcomes and rejection analysis |

Interactive documentation is available at:

`http://127.0.0.1:8000/docs`

---

## Data Generation

The project includes a synthetic data generator in:

`pipeline/synthetic_data.py`

It generates four related datasets:

- Customers
- Products
- Orders
- Order Items

The generator supports configurable record counts and a fixed random seed to make generated data reproducible.

Example usage:

```python
from pipeline.synthetic_data import (
    generate_all_data,
    save_data_to_csv,
)

data = generate_all_data(
    number_of_customers=100,
    number_of_products=50,
    number_of_orders=200,
    seed=42,
)

save_data_to_csv(data, "data/input")
```

The generated datasets maintain relationships between customers, orders, products, and order items.

---

## Edge-Case Testing and Rejection Analysis

Edge-case fixtures are generated separately from the production demonstration data.

Generate the fixtures:

```powershell
python -m scripts.generate_edge_cases
```

Run edge-case validation:

```powershell
python -m scripts.test_edge_cases
```

The test scenarios include:

- Valid records.
- Missing required values.
- Duplicate identifiers.
- Duplicate email addresses and SKUs.
- Invalid foreign-key references.
- Invalid allowed values.
- Numeric boundary violations.
- Zero and negative quantities.
- Invalid order totals.
- Late and out-of-order records.

### Edge-Case Results

| Metric | Result |
|---|---:|
| Total scenarios | 30 |
| Passed scenarios | 30 |
| Failed scenarios | 0 |
| Accepted records | 10 |
| Rejected records | 20 |

<badge color="success">30 of 30 scenarios passed</badge>

### Rejection Reports

The validation process produces:

- `reports/edge_case_rejection_analysis.csv`
- `reports/edge_case_rejection_summary.csv`

These reports contain scenario outcomes, failed validation rules, and rejection reasons.

---

## Large-Volume Data Validation

The project includes a separate large-volume data generation and validation workflow.

Generate the large datasets using:

```powershell
python -m scripts.generate_large_data
```

The default configuration generates:

- 10,000 customers.
- 5,000 products.
- 50,000 orders.
- 125,166 order items.

**Total: 190,166 records.**

Run large-volume validation:

```powershell
python -m scripts.run_large_validation
```

### Large-Volume Validation Results

| Dataset | Input | Accepted | Rejected |
|---|---:|---:|---:|
| Customers | 10,000 | 10,000 | 0 |
| Products | 5,000 | 5,000 | 0 |
| Orders | 50,000 | 50,000 | 0 |
| Order Items | 125,166 | 125,166 | 0 |
| **Total** | **190,166** | **190,166** | **0** |

### Reconciliation Results

- Input records: 190,166.
- Accepted records: 190,166.
- Rejected records: 0.
- Input reconciliation: Passed.
- Order totals checked: 50,000.
- Order total mismatches: 0.

The large-volume validation workflow is separate from the live PostgreSQL demonstration database.

### Generated Outputs

The process produces:

- Accepted datasets under `data/processed/large_input/`.
- Rejected datasets under `data/quarantine/large_input/`.
- `reports/large_validation_report.json`.
- `reports/large_order_total_reconciliation.csv`.

---

## Automated Testing

The project uses Pytest for automated testing.

Run the test suite:

```powershell
python -m pytest -v
```

### Current Test Coverage

**Validation Engine**

- Completeness checks.
- Uniqueness checks.
- Case-insensitive uniqueness.
- Range validation.
- Exclusive boundary checks.
- Referential integrity.
- Allowed-value validation.
- Missing-column error handling.
- Configured validation rule execution.
- Accepted and rejected record separation.
- WARNING versus ERROR severity behaviour.

**Synthetic Data Generator**

- Reproducible data generation.
- Dataset record counts.
- Customer-to-order relationships.
- Order-to-order-item relationships.
- Product-to-order-item relationships.
- Order-total calculations.
- Invalid generation parameter handling.

### Latest Verified Test Result

```text
18 passed
0 failed
```

Execution time: 1.97 seconds.

The dedicated pytest suite uses local DataFrames and does not modify PostgreSQL records.

---

## Assumptions and Limitations

- E-commerce is used as the demonstration domain.
- Validation logic is designed to be configuration-driven.
- CSV files are the current primary input format.
- Synthetic datasets are used for reproducible testing.
- Large-volume validation is performed separately from the live demonstration database.
- PostgreSQL must be configured locally.
- The current implementation focuses on structured data validation and pipeline execution.
- Performance depends on the local hardware and database configuration.

## Future Improvements

- Support additional structured file formats.
- Add additional data-source integrations.
- Introduce scheduled pipeline execution.
- Expand configurable validation rule types.
- Add performance benchmarking for larger datasets.
- Improve dashboard filtering and reporting.
- Add pipeline monitoring and alerting capabilities.
- Extend the framework to additional business domains.

---

## Project Summary

The Configurable Data Quality & Engineering Platform demonstrates an end-to-end data quality workflow with:

- Configuration-driven validation.
- Data ingestion and processing.
- Accepted and rejected record management.
- Quarantine and rejection analysis.
- PostgreSQL persistence.
- Pipeline execution tracking.
- FastAPI integration.
- Streamlit analytics.
- Automated testing.
- Edge-case validation.
- Large-volume data reconciliation.

The project demonstrates how a reusable data quality framework can improve data reliability, traceability, and visibility across structured-data engineering workflows.