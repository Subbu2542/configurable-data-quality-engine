
-- =====================================================
-- CONFIGURABLE DATA QUALITY ENGINE
-- PostgreSQL Database Schema
-- =====================================================

-- 1. Create logical schemas
CREATE SCHEMA IF NOT EXISTS platform;
CREATE SCHEMA IF NOT EXISTS ecommerce;


-- =====================================================
-- 2. PLATFORM METADATA TABLES
-- =====================================================

-- DATASETS
CREATE TABLE IF NOT EXISTS platform.datasets (
    dataset_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dataset_name VARCHAR(150) NOT NULL UNIQUE,
    source_type VARCHAR(30) NOT NULL,
    target_schema VARCHAR(100) NOT NULL,
    target_table VARCHAR(150) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_source_type
        CHECK (source_type IN ('CSV', 'API', 'DATABASE'))
);


-- DATASET SCHEMAS
CREATE TABLE IF NOT EXISTS platform.dataset_schemas (
    schema_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dataset_id UUID NOT NULL,
    schema_version INTEGER NOT NULL,
    schema_definition JSONB NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_dataset_schema
        FOREIGN KEY (dataset_id)
        REFERENCES platform.datasets(dataset_id),

    CONSTRAINT uq_dataset_schema_version
        UNIQUE (dataset_id, schema_version)
);


-- VALIDATION RULES
CREATE TABLE IF NOT EXISTS platform.validation_rules (
    rule_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dataset_id UUID NOT NULL,
    rule_name VARCHAR(150) NOT NULL,
    rule_type VARCHAR(50) NOT NULL,
    column_name VARCHAR(150),
    parameters JSONB NOT NULL DEFAULT '{}'::jsonb,
    severity VARCHAR(20) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_validation_dataset
        FOREIGN KEY (dataset_id)
        REFERENCES platform.datasets(dataset_id),

    CONSTRAINT uq_dataset_rule_name
        UNIQUE (dataset_id, rule_name),

    CONSTRAINT chk_rule_type
        CHECK (
            rule_type IN (
                'completeness',
                'uniqueness',
                'referential_integrity',
                'range',
                'freshness',
                'custom'
            )
        ),

    CONSTRAINT chk_rule_severity
        CHECK (
            severity IN (
                'CRITICAL',
                'HIGH',
                'MEDIUM',
                'LOW'
            )
        )
);


-- =====================================================
-- 3. PIPELINE EXECUTION TABLES
-- =====================================================

-- PIPELINE RUNS
CREATE TABLE IF NOT EXISTS platform.pipeline_runs (
    run_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dataset_id UUID NOT NULL,
    idempotency_key VARCHAR(255) NOT NULL,
    source_file VARCHAR(500),
    source_fingerprint VARCHAR(128),
    status VARCHAR(30) NOT NULL DEFAULT 'PENDING',

    input_count BIGINT NOT NULL DEFAULT 0,
    output_count BIGINT NOT NULL DEFAULT 0,
    rejected_count BIGINT NOT NULL DEFAULT 0,
    error_count BIGINT NOT NULL DEFAULT 0,

    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    failure_reason TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_pipeline_dataset
        FOREIGN KEY (dataset_id)
        REFERENCES platform.datasets(dataset_id),

    CONSTRAINT uq_dataset_idempotency
        UNIQUE (dataset_id, idempotency_key),

    CONSTRAINT chk_run_status
        CHECK (
            status IN (
                'PENDING',
                'RUNNING',
                'SUCCESS',
                'PARTIAL_SUCCESS',
                'FAILED'
            )
        ),

    CONSTRAINT chk_run_counts
        CHECK (
            input_count >= 0
            AND output_count >= 0
            AND rejected_count >= 0
            AND error_count >= 0
        )
);


-- VALIDATION RESULTS
CREATE TABLE IF NOT EXISTS platform.validation_results (
    result_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID NOT NULL,
    rule_id UUID NOT NULL,

    status VARCHAR(20) NOT NULL,
    total_records BIGINT NOT NULL DEFAULT 0,
    passed_records BIGINT NOT NULL DEFAULT 0,
    failed_records BIGINT NOT NULL DEFAULT 0,

    severity VARCHAR(20) NOT NULL,
    execution_time_ms NUMERIC(14,3),
    failure_reason TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_result_run
        FOREIGN KEY (run_id)
        REFERENCES platform.pipeline_runs(run_id),

    CONSTRAINT fk_result_rule
        FOREIGN KEY (rule_id)
        REFERENCES platform.validation_rules(rule_id),

    CONSTRAINT uq_run_rule
        UNIQUE (run_id, rule_id),

    CONSTRAINT chk_result_status
        CHECK (status IN ('PASS', 'FAIL', 'ERROR')),

    CONSTRAINT chk_result_counts
        CHECK (
            total_records >= 0
            AND passed_records >= 0
            AND failed_records >= 0
            AND passed_records + failed_records = total_records
        ),

    CONSTRAINT chk_result_severity
        CHECK (
            severity IN (
                'CRITICAL',
                'HIGH',
                'MEDIUM',
                'LOW'
            )
        )
);


-- QUARANTINE RECORDS
CREATE TABLE IF NOT EXISTS platform.quarantine_records (
    quarantine_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID NOT NULL,
    dataset_id UUID NOT NULL,

    source_file VARCHAR(500),
    source_record_id VARCHAR(255),
    record_data JSONB NOT NULL,
    failed_rule_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    rejection_reason TEXT NOT NULL,

    rejected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_quarantine_run
        FOREIGN KEY (run_id)
        REFERENCES platform.pipeline_runs(run_id),

    CONSTRAINT fk_quarantine_dataset
        FOREIGN KEY (dataset_id)
        REFERENCES platform.datasets(dataset_id),

    CONSTRAINT uq_quarantine_record
        UNIQUE (run_id, source_record_id)
);


-- PIPELINE LOGS
CREATE TABLE IF NOT EXISTS platform.pipeline_logs (
    log_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    run_id UUID NOT NULL,

    log_level VARCHAR(20) NOT NULL,
    stage VARCHAR(100) NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_log_run
        FOREIGN KEY (run_id)
        REFERENCES platform.pipeline_runs(run_id),

    CONSTRAINT chk_log_level
        CHECK (
            log_level IN (
                'DEBUG',
                'INFO',
                'WARNING',
                'ERROR',
                'CRITICAL'
            )
        )
);


-- =====================================================
-- 4. E-COMMERCE TARGET TABLES
-- =====================================================

-- CUSTOMERS
CREATE TABLE IF NOT EXISTS ecommerce.customers (
    customer_id BIGINT PRIMARY KEY,
    customer_name VARCHAR(150) NOT NULL,
    email VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    city VARCHAR(100),

    source_file VARCHAR(500) NOT NULL,
    source_record_id VARCHAR(255) NOT NULL,
    run_id UUID NOT NULL,

    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_customer_run
        FOREIGN KEY (run_id)
        REFERENCES platform.pipeline_runs(run_id),

    CONSTRAINT uq_customer_source_record
        UNIQUE (source_file, source_record_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS
    idx_customers_email_lower
    ON ecommerce.customers (LOWER(email));


-- PRODUCTS
CREATE TABLE IF NOT EXISTS ecommerce.products (
    product_id BIGINT PRIMARY KEY,
    product_name VARCHAR(200) NOT NULL,
    sku VARCHAR(100) NOT NULL UNIQUE,
    category VARCHAR(100) NOT NULL,
    price NUMERIC(12,2) NOT NULL,

    source_file VARCHAR(500) NOT NULL,
    source_record_id VARCHAR(255) NOT NULL,
    run_id UUID NOT NULL,

    created_at TIMESTAMPTZ NOT NULL,
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_product_run
        FOREIGN KEY (run_id)
        REFERENCES platform.pipeline_runs(run_id),

    CONSTRAINT uq_product_source_record
        UNIQUE (source_file, source_record_id),

    CONSTRAINT chk_product_price
        CHECK (price > 0)
);


-- ORDERS
CREATE TABLE IF NOT EXISTS ecommerce.orders (
    order_id BIGINT PRIMARY KEY,
    customer_id BIGINT NOT NULL,
    order_date TIMESTAMPTZ NOT NULL,
    order_status VARCHAR(30) NOT NULL,
    total_amount NUMERIC(12,2) NOT NULL,

    source_file VARCHAR(500) NOT NULL,
    source_record_id VARCHAR(255) NOT NULL,
    run_id UUID NOT NULL,

    created_at TIMESTAMPTZ NOT NULL,
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_order_customer
        FOREIGN KEY (customer_id)
        REFERENCES ecommerce.customers(customer_id),

    CONSTRAINT fk_order_run
        FOREIGN KEY (run_id)
        REFERENCES platform.pipeline_runs(run_id),

    CONSTRAINT uq_order_source_record
        UNIQUE (source_file, source_record_id),

    CONSTRAINT chk_order_amount
        CHECK (total_amount >= 0),

    CONSTRAINT chk_order_status
        CHECK (
            order_status IN (
                'PLACED',
                'PROCESSING',
                'SHIPPED',
                'DELIVERED',
                'CANCELLED'
            )
        )
);


-- ORDER ITEMS
CREATE TABLE IF NOT EXISTS ecommerce.order_items (
    order_item_id BIGINT PRIMARY KEY,
    order_id BIGINT NOT NULL,
    product_id BIGINT NOT NULL,

    quantity INTEGER NOT NULL,
    unit_price NUMERIC(12,2) NOT NULL,

    line_total NUMERIC(14,2)
        GENERATED ALWAYS AS (quantity * unit_price) STORED,

    source_file VARCHAR(500) NOT NULL,
    source_record_id VARCHAR(255) NOT NULL,
    run_id UUID NOT NULL,

    ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_item_order
        FOREIGN KEY (order_id)
        REFERENCES ecommerce.orders(order_id),

    CONSTRAINT fk_item_product
        FOREIGN KEY (product_id)
        REFERENCES ecommerce.products(product_id),

    CONSTRAINT fk_item_run
        FOREIGN KEY (run_id)
        REFERENCES platform.pipeline_runs(run_id),

    CONSTRAINT uq_item_source_record
        UNIQUE (source_file, source_record_id),

    CONSTRAINT chk_item_quantity
        CHECK (quantity > 0),

    CONSTRAINT chk_item_price
        CHECK (unit_price >= 0)
);


-- =====================================================
-- 5. PERFORMANCE INDEXES
-- =====================================================

CREATE INDEX IF NOT EXISTS idx_rules_dataset
    ON platform.validation_rules(dataset_id);

CREATE INDEX IF NOT EXISTS idx_runs_dataset_created
    ON platform.pipeline_runs(dataset_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_results_run
    ON platform.validation_results(run_id);

CREATE INDEX IF NOT EXISTS idx_quarantine_run
    ON platform.quarantine_records(run_id);

CREATE INDEX IF NOT EXISTS idx_logs_run_created
    ON platform.pipeline_logs(run_id, created_at);

CREATE INDEX IF NOT EXISTS idx_orders_customer
    ON ecommerce.orders(customer_id);

CREATE INDEX IF NOT EXISTS idx_order_items_order
    ON ecommerce.order_items(order_id);

CREATE INDEX IF NOT EXISTS idx_order_items_product
    ON ecommerce.order_items(product_id);


-- =====================================================
-- END OF DATABASE SCHEMA
-- =====================================================
