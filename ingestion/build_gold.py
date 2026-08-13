"""Gold: (re)build the serving layer from silver. Cheap enough to run every pipeline pass."""
from pathlib import Path

from db import connect

SCHEMA_SQL_PATH = Path(__file__).resolve().parent.parent / "db" / "schema_gold.sql"


def build(con):
    for stmt in SCHEMA_SQL_PATH.read_text().split(";\n\n"):
        stmt = stmt.strip()
        if stmt:
            con.execute(stmt)
    n_lines = con.execute("SELECT count(*) FROM gold.dim_lines").fetchone()[0]
    n_stations = con.execute("SELECT count(*) FROM gold.dim_stations").fetchone()[0]
    print(f"[gold] dim_lines={n_lines} rows, dim_stations={n_stations} rows, v_scheduled_departures rebuilt")


if __name__ == "__main__":
    con = connect()
    build(con)
    con.close()
