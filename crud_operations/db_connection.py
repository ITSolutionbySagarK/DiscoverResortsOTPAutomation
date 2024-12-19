import pyodbc
import os

def get_db_connection():
    """Establishes a connection to Azure SQL."""
    connection_string = os.getenv("SQL_CONNECTION_STRING")
    return pyodbc.connect(connection_string)
