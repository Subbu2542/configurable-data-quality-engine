
import pandas as pd


def check_completeness(df, column):
    """
    Identify records where a required column is NULL or empty.
    """
    if column not in df.columns:
        raise ValueError(f"Column '{column}' does not exist.")

    values = df[column]

    failed = values.isna()

    if pd.api.types.is_string_dtype(values):
        failed = failed | values.astype("string").str.strip().eq("").fillna(False)

    return failed


def check_uniqueness(df, column, case_insensitive=False):
    """
    Identify duplicate values in a column.
    All occurrences of a duplicated value are flagged.
    """
    if column not in df.columns:
        raise ValueError(f"Column '{column}' does not exist.")

    values = df[column]

    if case_insensitive:
        values = values.astype("string").str.strip().str.casefold()

    failed = values.duplicated(keep=False)

    return failed.fillna(False)


def check_range(
    df,
    column,
    minimum=None,
    maximum=None,
    exclusive_minimum=False,
    exclusive_maximum=False
):
    """
    Identify values outside the configured range.
    """

    if column not in df.columns:
        raise ValueError(f"Column '{column}' does not exist.")

    values = pd.to_numeric(df[column], errors="coerce")

    failed = values.isna()

    if minimum is not None:
        if exclusive_minimum:
            failed = failed | (values <= minimum)
        else:
            failed = failed | (values < minimum)

    if maximum is not None:
        if exclusive_maximum:
            failed = failed | (values >= maximum)
        else:
            failed = failed | (values > maximum)

    return failed



def check_referential_integrity(
    source_df,
    source_column,
    reference_df,
    reference_column
):
    """
    Fail records whose foreign-key value is missing
    or does not exist in the reference dataset.
    """

    if source_column not in source_df.columns:
        raise ValueError(f"Column '{source_column}' does not exist.")

    if reference_column not in reference_df.columns:
        raise ValueError(
            f"Reference column '{reference_column}' does not exist."
        )

    source_values = source_df[source_column]

    missing = source_values.isna()

    if pd.api.types.is_string_dtype(source_values):
        blank = (
            source_values.astype("string")
            .str.strip()
            .eq("")
            .fillna(False)
        )
        missing = missing | blank

    reference_values = set(
        reference_df[reference_column].dropna().tolist()
    )

    failed = missing | ~source_values.isin(reference_values)

    return failed


def check_allowed_values(df, column, allowed_values):
    """
    Identify records containing values outside the allowed list.
    """

    if column not in df.columns:
        raise ValueError(f"Column '{column}' does not exist.")

    failed = ~df[column].isin(allowed_values)

    return failed


def execute_validation_rule(
    df,
    rule_type,
    column_name,
    parameters
):
    """
    Execute a validation based on its configured rule type.
    Returns a Boolean Series:
    True = failed, False = passed.
    """

    if rule_type == "COMPLETENESS":
        return check_completeness(df, column_name)

    elif rule_type == "UNIQUENESS":
        return check_uniqueness(
            df,
            column_name,
            case_insensitive=parameters.get(
                "case_insensitive", False
            )
        )

    elif rule_type == "RANGE":
        return check_range(
            df,
            column_name,
            minimum=parameters.get("minimum"),
            maximum=parameters.get("maximum"),
            exclusive_minimum=parameters.get(
                "exclusive_minimum", False
            ),
            exclusive_maximum=parameters.get(
                "exclusive_maximum", False
            )
        )

    elif rule_type == "VALUE_CHECK":
        return check_allowed_values(
            df,
            column_name,
            parameters.get("allowed_values", [])
        )

    else:
        raise ValueError(
            f"Unsupported validation rule type: {rule_type}"
        )



def run_dataset_validations(
    df,
    rules,
    reference_dataframes=None
):
    """
    Execute configured validation rules against a dataset.
    Referential integrity rules use reference DataFrames.
    """

    reference_dataframes = reference_dataframes or {}
    results = []

    for rule in rules:
        rule_type = rule["rule_type"]
        column_name = rule["column_name"]
        parameters = rule["parameters"]

        if rule_type == "REFERENTIAL_INTEGRITY":

            reference_dataset = parameters.get("reference_dataset")
            reference_column = parameters.get("reference_column")

            if reference_dataset not in reference_dataframes:
                raise ValueError(
                    f"Reference dataset '{reference_dataset}' "
                    "was not provided."
                )

            reference_df = reference_dataframes[reference_dataset]

            failed = check_referential_integrity(
                source_df=df,
                source_column=column_name,
                reference_df=reference_df,
                reference_column=reference_column
            )

        else:
            failed = execute_validation_rule(
                df=df,
                rule_type=rule_type,
                column_name=column_name,
                parameters=parameters
            )

        total_records = len(df)
        failed_records = int(failed.sum())
        passed_records = total_records - failed_records

        results.append({
            "rule_id": str(rule["rule_id"]),
            "rule_name": rule["rule_name"],
            "rule_type": rule_type,
            "column_name": column_name,
            "severity": rule["severity"],
            "total_records": total_records,
            "passed_records": passed_records,
            "failed_records": failed_records,
            "status": "FAIL" if failed_records > 0 else "PASS"
        })

    return results


def validate_dataset_records(
    df,
    rules,
    reference_dataframes=None,
    source_file=None
):
    """
    Run configured rules and separate accepted and rejected records.
    ERROR rules cause rejection. WARNING rules do not.
    """

    if not source_file:
        raise ValueError("source_file must be provided.")

    reference_dataframes = reference_dataframes or {}

    validation_results = []
    failed_rule_ids = [[] for _ in range(len(df))]
    rejection_reasons = [[] for _ in range(len(df))]

    for rule in rules:
        rule_type = rule["rule_type"]
        column_name = rule["column_name"]
        parameters = rule["parameters"]
        severity = rule["severity"].upper()

        if rule_type == "REFERENTIAL_INTEGRITY":
            reference_dataset = parameters["reference_dataset"]
            reference_column = parameters["reference_column"]

            if reference_dataset not in reference_dataframes:
                raise ValueError(
                    f"Reference dataset '{reference_dataset}' was not provided."
                )

            failed = check_referential_integrity(
                source_df=df,
                source_column=column_name,
                reference_df=reference_dataframes[reference_dataset],
                reference_column=reference_column
            )
        else:
            failed = execute_validation_rule(
                df=df,
                rule_type=rule_type,
                column_name=column_name,
                parameters=parameters
            )

        failed_mask = failed.fillna(True).to_numpy(dtype=bool)
        failed_positions = [
            position
            for position, is_failed in enumerate(failed_mask)
            if is_failed
        ]

        for position in failed_positions:
            if severity == "ERROR":
                failed_rule_ids[position].append(str(rule["rule_id"]))
                rejection_reasons[position].append(rule["rule_name"])

        failed_count = len(failed_positions)

        validation_results.append({
            "rule_id": str(rule["rule_id"]),
            "rule_name": rule["rule_name"],
            "rule_type": rule_type,
            "column_name": column_name,
            "severity": severity,
            "total_records": len(df),
            "passed_records": len(df) - failed_count,
            "failed_records": failed_count,
            "status": "FAIL" if failed_count else "PASS"
        })

    rejected_positions = [
        position
        for position, rule_ids in enumerate(failed_rule_ids)
        if rule_ids
    ]

    accepted_positions = [
        position
        for position in range(len(df))
        if position not in set(rejected_positions)
    ]

    file_name = source_file.replace("\\", "/").split("/")[-1]

    accepted_records = df.iloc[accepted_positions].copy()
    rejected_records = df.iloc[rejected_positions].copy()

    accepted_records["source_file"] = source_file
    rejected_records["source_file"] = source_file

    accepted_records["source_record_id"] = [
        f"{file_name}:record:{position + 1}"
        for position in accepted_positions
    ]

    rejected_records["source_record_id"] = [
        f"{file_name}:record:{position + 1}"
        for position in rejected_positions
    ]

    rejected_records["failed_rule_ids"] = [
        failed_rule_ids[position]
        for position in rejected_positions
    ]

    rejected_records["rejection_reason"] = [
        "; ".join(rejection_reasons[position])
        for position in rejected_positions
    ]

    return {
        "validation_results": validation_results,
        "accepted_records": accepted_records,
        "rejected_records": rejected_records
    }
