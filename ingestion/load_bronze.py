"""Bronze: load raw GTFS static CSVs (from the landed ZIP) into DuckDB, untyped.

Each run appends a new batch (tagged _batch_id) rather than overwriting, so bronze
keeps full history of what was ingested. Silver always reads only the latest batch.
"""
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

import duckdb

from config import GTFS_STATIC_BRONZE_DIR, GTFS_STATIC_TABLES, RAIL_CATEGORY
from db import connect

SCHEMA_SQL_PATH = Path(__file__).resolve().parent.parent / "db" / "schema_bronze.sql"


def load(con, category: str, batch_id: str | None = None) -> str:
    zip_path = GTFS_STATIC_BRONZE_DIR / category / "latest.zip"
    if not zip_path.exists():
        raise FileNotFoundError(f"No bronze zip for {category} at {zip_path}. Run fetch_gtfs_static.py first.")

    batch_id = batch_id or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    loaded_at = datetime.now(timezone.utc)

    con.execute(SCHEMA_SQL_PATH.read_text())

    with TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        with zipfile.ZipFile(zip_path) as zf:
            for name in zf.namelist():
                if name.startswith("__MACOSX/") or name.endswith("/"):
                    continue
                zf.extract(name, tmp_path)

        for table in GTFS_STATIC_TABLES:
            csv_path = tmp_path / f"{table}.txt"
            if not csv_path.exists():
                print(f"[bronze]   {category}: {table}.txt not present, skipping")
                continue

            cols = con.execute(f"DESCRIBE bronze.gtfs_{table}").fetchall()
            data_cols = [c[0] for c in cols if not c[0].startswith("_")]
            col_list = ", ".join(f'"{c}"' for c in data_cols)

            con.execute(
                f"""
                INSERT INTO bronze.gtfs_{table} BY NAME
                SELECT {col_list}, ? AS _category, ? AS _batch_id, ? AS _loaded_at
                FROM read_csv(?, all_varchar=true, header=true)
                """,
                [category, batch_id, loaded_at, str(csv_path)],
            )
            n = con.execute(
                "SELECT count(*) FROM bronze.gtfs_%s WHERE _batch_id = ?" % table, [batch_id]
            ).fetchone()[0]
            print(f"[bronze]   {category}: gtfs_{table} += {n} rows (batch {batch_id})")

    return batch_id


if __name__ == "__main__":
    categories = sys.argv[1:] or [RAIL_CATEGORY]
    con = connect()
    for cat in categories:
        load(con, cat)
    con.close()
