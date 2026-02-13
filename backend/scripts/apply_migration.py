import os
import sys
from sqlalchemy import create_engine, text

# Add current directory to path so imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.api.database import DATABASE_URL


def apply_migration(migration_file: str):
    print(f"Applying migration: {migration_file}")

    # Read SQL
    try:
        with open(migration_file, "r") as f:
            sql = f.read()
    except FileNotFoundError:
        print(f"Error: File {migration_file} not found.")
        return

    # Connect to DB
    engine = create_engine(DATABASE_URL)
    with engine.connect() as connection:
        with connection.begin():
            # Split statements if necessary, but here we just have one
            # text() is needed for raw sql execution
            connection.execute(text(sql))

    print("Migration applied successfully.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python apply_migration.py <path_to_sql_file>")
        sys.exit(1)

    apply_migration(sys.argv[1])
