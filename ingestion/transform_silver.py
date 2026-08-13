"""Silver: typed, conformed tables built from the latest bronze batch per category.

GTFS clock times (HH:MM:SS, where HH may exceed 23 for past-midnight service) are
kept as text and also parsed into seconds-since-midnight for arithmetic.
"""
import sys

from config import RAIL_CATEGORY
from db import connect

TIME_TO_SECONDS = """
    CAST(split_part(t, ':', 1) AS INTEGER) * 3600
    + CAST(split_part(t, ':', 2) AS INTEGER) * 60
    + CAST(split_part(t, ':', 3) AS INTEGER)
"""


def _latest_batch_filter(con, table: str, category: str) -> str:
    batch_id = con.execute(
        f"SELECT max(_batch_id) FROM bronze.gtfs_{table} WHERE _category = ?", [category]
    ).fetchone()[0]
    if batch_id is None:
        raise RuntimeError(f"No bronze data for gtfs_{table} / {category}. Run load_bronze.py first.")
    return batch_id


def transform(con, category: str):
    b = {t: _latest_batch_filter(con, t, category) for t in [
        "agency", "routes", "stops", "trips", "stop_times", "calendar", "frequencies", "shapes",
    ]}

    con.execute(
        """
        CREATE OR REPLACE TABLE silver.dim_agency AS
        SELECT agency_id, agency_name, agency_url, agency_timezone, agency_phone, agency_lang,
               _category AS category
        FROM bronze.gtfs_agency WHERE _category = ? AND _batch_id = ?
        """,
        [category, b["agency"]],
    )

    con.execute(
        """
        CREATE OR REPLACE TABLE silver.dim_routes AS
        SELECT route_id, agency_id, route_short_name AS short_name, route_long_name AS long_name,
               route_desc AS description, CAST(route_type AS INTEGER) AS route_type,
               route_color AS color, route_text_color AS text_color,
               category AS mode, status, _category AS source_category
        FROM bronze.gtfs_routes WHERE _category = ? AND _batch_id = ?
        """,
        [category, b["routes"]],
    )

    con.execute(
        """
        CREATE OR REPLACE TABLE silver.dim_stops AS
        SELECT stop_id, stop_name AS name, CAST(stop_lat AS DOUBLE) AS lat, CAST(stop_lon AS DOUBLE) AS lon,
               category AS mode, route_id AS primary_route_id,
               CAST(isOKU AS BOOLEAN) AS wheelchair_accessible, status, _category AS source_category
        FROM bronze.gtfs_stops WHERE _category = ? AND _batch_id = ?
        """,
        [category, b["stops"]],
    )

    con.execute(
        """
        CREATE OR REPLACE TABLE silver.dim_calendar AS
        SELECT service_id, CAST(monday AS BOOLEAN) AS monday, CAST(tuesday AS BOOLEAN) AS tuesday,
               CAST(wednesday AS BOOLEAN) AS wednesday, CAST(thursday AS BOOLEAN) AS thursday,
               CAST(friday AS BOOLEAN) AS friday, CAST(saturday AS BOOLEAN) AS saturday,
               CAST(sunday AS BOOLEAN) AS sunday,
               strptime(start_date, '%Y%m%d')::DATE AS start_date,
               strptime(end_date, '%Y%m%d')::DATE AS end_date
        FROM bronze.gtfs_calendar WHERE _category = ? AND _batch_id = ?
        """,
        [category, b["calendar"]],
    )

    con.execute(
        """
        CREATE OR REPLACE TABLE silver.dim_trips AS
        SELECT trip_id, route_id, service_id, trip_headsign AS headsign,
               CAST(direction_id AS INTEGER) AS direction_id, shape_id
        FROM bronze.gtfs_trips WHERE _category = ? AND _batch_id = ?
        """,
        [category, b["trips"]],
    )

    con.execute(
        f"""
        CREATE OR REPLACE TABLE silver.fact_stop_times AS
        SELECT trip_id, route_id, CAST(direction_id AS INTEGER) AS direction_id, stop_id,
               CAST(stop_sequence AS INTEGER) AS stop_sequence,
               arrival_time, departure_time,
               ({TIME_TO_SECONDS.replace('t,', 'arrival_time,')}) AS arrival_seconds,
               ({TIME_TO_SECONDS.replace('t,', 'departure_time,')}) AS departure_seconds
        FROM bronze.gtfs_stop_times WHERE _category = ? AND _batch_id = ?
        """,
        [category, b["stop_times"]],
    )

    con.execute(
        f"""
        CREATE OR REPLACE TABLE silver.fact_frequencies AS
        SELECT trip_id, start_time, end_time, CAST(headway_secs AS INTEGER) AS headway_secs,
               ({TIME_TO_SECONDS.replace('t,', 'start_time,')}) AS start_seconds,
               ({TIME_TO_SECONDS.replace('t,', 'end_time,')}) AS end_seconds
        FROM bronze.gtfs_frequencies WHERE _category = ? AND _batch_id = ?
        """,
        [category, b["frequencies"]],
    )

    con.execute(
        """
        CREATE OR REPLACE TABLE silver.dim_shapes AS
        SELECT shape_id, CAST(shape_pt_sequence AS INTEGER) AS pt_sequence,
               CAST(shape_pt_lat AS DOUBLE) AS lat, CAST(shape_pt_lon AS DOUBLE) AS lon
        FROM bronze.gtfs_shapes WHERE _category = ? AND _batch_id = ?
        """,
        [category, b["shapes"]],
    )

    print(f"[silver] rebuilt dim/fact tables for {category} from batches: {b}")


if __name__ == "__main__":
    categories = sys.argv[1:] or [RAIL_CATEGORY]
    con = connect()
    for cat in categories:
        transform(con, cat)
    con.close()
