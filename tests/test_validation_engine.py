import pandas as pd
import pytest

from pipeline.validation.engine import (
    check_completeness,
    check_uniqueness,
    check_range,
    check_referential_integrity,
    check_allowed_values,
    execute_validation_rule,
    validate_dataset_records,
)


def test_completeness_detects_null_and_blank_values():
    df = pd.DataFrame({"name": ["Ravi", None, "", "  "]})
    result = check_completeness(df, "name")
    assert result.tolist() == [False, True, True, True]


def test_uniqueness_detects_all_duplicate_values():
    df = pd.DataFrame({"email": ["a@test.com", "b@test.com", "a@test.com"]})
    result = check_uniqueness(df, "email")
    assert result.tolist() == [True, False, True]


def test_uniqueness_supports_case_insensitive_comparison():
    df = pd.DataFrame({"email": ["User@test.com", "user@test.com"]})
    result = check_uniqueness(df, "email", case_insensitive=True)
    assert result.tolist() == [True, True]


def test_range_detects_values_outside_inclusive_bounds():
    df = pd.DataFrame({"price": [0, 10, 50, 100, 101]})
    result = check_range(df, "price", minimum=10, maximum=100)
    assert result.tolist() == [True, False, False, False, True]


def test_range_detects_non_numeric_values():
    df = pd.DataFrame({"price": [10, "invalid", 20]})
    result = check_range(df, "price", minimum=0, maximum=100)
    assert result.tolist() == [False, True, False]


def test_range_supports_exclusive_minimum():
    df = pd.DataFrame({"quantity": [0, 1, 2]})
    result = check_range(
        df, "quantity", minimum=0, exclusive_minimum=True
    )
    assert result.tolist() == [True, False, False]


def test_referential_integrity_detects_missing_references():
    source = pd.DataFrame({"customer_id": [1, 2, None, 4]})
    reference = pd.DataFrame({"customer_id": [1, 2, 3]})

    result = check_referential_integrity(
        source, "customer_id", reference, "customer_id"
    )
    assert result.tolist() == [False, False, True, True]


def test_allowed_values_detects_invalid_status():
    df = pd.DataFrame({"status": ["PLACED", "SHIPPED", "UNKNOWN"]})
    result = check_allowed_values(
        df, "status", ["PLACED", "SHIPPED", "DELIVERED"]
    )
    assert result.tolist() == [False, False, True]


def test_missing_column_raises_value_error():
    df = pd.DataFrame({"name": ["Ravi"]})
    with pytest.raises(ValueError):
        check_completeness(df, "email")


def test_execute_validation_rule_uses_configured_parameters():
    df = pd.DataFrame({"price": [10, 20, 150]})
    result = execute_validation_rule(
        df,
        "RANGE",
        "price",
        {"minimum": 0, "maximum": 100},
    )
    assert result.tolist() == [False, False, True]


def test_validate_dataset_records_separates_accepted_and_rejected():
    df = pd.DataFrame({
        "customer_id": [1, 2, 3],
        "email": ["a@test.com", "", "c@test.com"],
    })

    rules = [
        {
            "rule_id": "R1",
            "rule_name": "Email completeness",
            "rule_type": "COMPLETENESS",
            "column_name": "email",
            "parameters": {},
            "severity": "ERROR",
        }
    ]

    result = validate_dataset_records(
        df, rules, source_file="customers.csv"
    )

    assert len(result["accepted_records"]) == 2
    assert len(result["rejected_records"]) == 1
    assert result["rejected_records"].iloc[0]["customer_id"] == 2
    assert result["rejected_records"].iloc[0]["rejection_reason"] == (
        "Email completeness"
    )
    assert result["rejected_records"].iloc[0]["source_record_id"] == (
        "customers.csv:record:2"
    )


def test_warning_rule_does_not_reject_record():
    df = pd.DataFrame({"price": [-5, 20]})

    rules = [
        {
            "rule_id": "R2",
            "rule_name": "Price warning",
            "rule_type": "RANGE",
            "column_name": "price",
            "parameters": {"minimum": 0},
            "severity": "WARNING",
        }
    ]

    result = validate_dataset_records(
        df, rules, source_file="products.csv"
    )

    assert len(result["accepted_records"]) == 2
    assert len(result["rejected_records"]) == 0
