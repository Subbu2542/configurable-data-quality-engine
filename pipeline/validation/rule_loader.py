
from sqlalchemy import text

from backend.services.database import engine


def load_validation_rules(dataset_name):
    """
    Retrieve active validation rules for a dataset
    from PostgreSQL.
    """

    query = text("""
        SELECT
            d.dataset_name,
            v.rule_id,
            v.rule_name,
            v.rule_type,
            v.column_name,
            v.parameters,
            v.severity
        FROM platform.validation_rules v
        JOIN platform.datasets d
            ON d.dataset_id = v.dataset_id
        WHERE d.dataset_name = :dataset_name
          AND v.is_active = TRUE
        ORDER BY v.rule_name
    """)

    with engine.connect() as connection:
        result = connection.execute(
            query,
            {"dataset_name": dataset_name}
        )

        return [dict(row) for row in result.mappings()]
