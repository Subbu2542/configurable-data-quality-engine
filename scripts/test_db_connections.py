from backend.services.database import test_connection

try:
    version = test_connection()

    print("PostgreSQL connection successful!")
    print("Database server version:")
    print(version)

except Exception as error:
    print("PostgreSQL connection failed.")
    print("Error:", error)