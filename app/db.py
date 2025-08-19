import sqlite3
from .utils import load_json


# Setup SQLite
def create_db_from_json(json_file, db_file="db/roles.db") -> sqlite3.Connection:
    """
    Create a SQLite database from a JSON file.
    Args:
        json_file (str): The path to the JSON file.
        db_file (str): The path to the SQLite database file.
    Returns:
        sqlite3.Connection: The SQLite connection object.
    """

    # Load JSON data
    data = load_json(json_file)

    # Initialize SQLite
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()

    # Create table (role_number as primary key, description as text)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS roles (
        role_number TEXT PRIMARY KEY,
        description TEXT
    )
    """)

    # Insert JSON data
    for role_number, description in data.items():
        cur.execute(
            "INSERT OR REPLACE INTO roles (role_number, description) VALUES (?, ?)",
            (role_number, description)
        )

    # Commit changes and close connection
    conn.commit()
    return conn


# Query Pipelines
def search_by_role_number(conn, role_number) -> str:
    """
    Search for a role description by role number.
    Args:
        conn (sqlite3.Connection): The SQLite connection object.
        role_number (str): The role number to search for.
    Returns:
        str: The role description, or None if not found.
    """
    cur = conn.cursor()
    cur.execute("SELECT description FROM roles WHERE role_number=?", (role_number,))
    return cur.fetchone()




# Example Usage 
if __name__ == "__main__":
    json_file = "dump/roles.json"  # Your JSON file
    db_file = "roles.db"

    # Create DB and load JSON data
    conn = create_db_from_json(json_file, db_file)

    # Basic queries
    print("\nSearch by Role Number 1111.0100:")
    print(search_by_role_number(conn, "1111.0100"))

    conn.close()
