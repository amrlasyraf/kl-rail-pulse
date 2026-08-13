import duckdb

from config import WAREHOUSE_PATH


def connect():
    WAREHOUSE_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(WAREHOUSE_PATH))
    con.execute("CREATE SCHEMA IF NOT EXISTS bronze")
    con.execute("CREATE SCHEMA IF NOT EXISTS silver")
    con.execute("CREATE SCHEMA IF NOT EXISTS gold")
    return con
