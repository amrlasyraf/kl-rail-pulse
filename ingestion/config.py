from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
BRONZE_DIR = DATA_DIR / "bronze"
GTFS_STATIC_BRONZE_DIR = BRONZE_DIR / "gtfs_static"
GTFS_REALTIME_BRONZE_DIR = BRONZE_DIR / "gtfs_realtime"
WAREHOUSE_PATH = DATA_DIR / "warehouse.duckdb"

GTFS_STATIC_URL = "https://api.data.gov.my/gtfs-static/prasarana"
GTFS_REALTIME_VEHICLE_POSITION_URL = "https://api.data.gov.my/gtfs-realtime/vehicle-position/prasarana"

# Rail is the project's primary focus. Bus categories are kept here because they
# are the only ones with a live GTFS-Realtime feed today (rail realtime is not
# published yet — see README), useful for exercising the realtime pipeline early.
RAIL_CATEGORY = "rapid-rail-kl"
REALTIME_CATEGORIES = ["rapid-bus-kl", "rapid-bus-mrtfeeder"]

GTFS_STATIC_TABLES = [
    "agency",
    "routes",
    "stops",
    "trips",
    "stop_times",
    "calendar",
    "frequencies",
    "shapes",
]
