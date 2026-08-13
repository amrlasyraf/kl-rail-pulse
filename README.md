# KL Rail Pulse

Klang Valley MRT/LRT status and (eventually) reliability platform, built on
official Malaysia open data (`data.gov.my`). Rail (Prasarana LRT/MRT/Monorail)
is the primary focus.

## Data sources

- **GTFS Static** — `https://api.data.gov.my/gtfs-static/prasarana?category=rapid-rail-kl`
  Stations, routes, trips, stop times, calendars, frequencies, shapes for all 8
  Prasarana rail lines (LRT Ampang/Kelana Jaya/Sri Petaling/Shah Alam, MRT
  Kajang/Putrajaya, KL Monorail, BRT Sunway).
- **GTFS-Realtime** — `https://api.data.gov.my/gtfs-realtime/vehicle-position/prasarana`
  **Rail has no realtime feed yet** (`category=rapid-rail-kl` returns 404: "Vehicle
  Position feed ... does not exist"). Only bus categories (`rapid-bus-kl`,
  `rapid-bus-mrtfeeder`, `rapid-bus-kuantan`, `rapid-bus-penang`) currently publish
  vehicle positions, updated every 30s. Trip updates and service alerts are not
  published for any category yet ("in our pipeline for 2026" per the API docs).
  Until rail realtime ships, "next arrival" in this app is a **scheduled**
  prediction derived from GTFS static, clearly labeled as such everywhere it's
  shown — not a live GPS-based ETA.
- **Historical ridership** — `ridership_od_rapidrail_daily` (daily MRT/LRT
  origin-destination counts) — not yet wired up; earmarked for the reliability/
  history side of the site.

## Architecture — medallion (bronze / silver / gold)

Local warehouse is a single DuckDB file (`data/warehouse.duckdb`) with three
schemas. Production is intended to move onto Supabase (Postgres) unchanged —
DuckDB's SQL dialect stays close to Postgres.

```
data.gov.my (GTFS static ZIP)
        │
        ▼
  data/bronze/gtfs_static/<category>/<batch>.zip   (raw file landing, immutable)
        │  ingestion/fetch_gtfs_static.py
        ▼
  bronze.gtfs_*                                     (untyped, one batch per run,
        │  ingestion/load_bronze.py                  full history kept)
        ▼
  silver.dim_*, silver.fact_*                        (typed, deduped to latest
        │  ingestion/transform_silver.py              batch per category)
        ▼
  gold.dim_lines, gold.dim_stations,                  (serving layer: business-
  gold.v_scheduled_departures                          ready, what the API reads)
        │  ingestion/build_gold.py
        ▼
  api/main.py (FastAPI)  →  web/static/index.html
```

`gold.v_scheduled_departures` expands `frequencies.txt` (headway-based service —
Prasarana publishes one template trip per direction/service pattern plus a
headway, not one row per physical run) into individual predicted stop-level
departure times, using `generate_series` over each headway band.

## Running locally

```bash
pip install -r requirements.txt

# Bronze -> silver -> gold for rail (re-run any time to refresh the schedule)
python ingestion/run_pipeline.py rapid-rail-kl

# API + static frontend (served from the same FastAPI app)
python -m uvicorn api.main:app --reload
# open http://127.0.0.1:8000/
```

## API

| Endpoint | Description |
|---|---|
| `GET /api/health` | liveness + server time |
| `GET /api/lines` | all rail lines with color, mode, station count |
| `GET /api/stations?route_id=` | stations, optionally filtered by line |
| `GET /api/stations/{stop_id}/departures` | next scheduled departures at a station (`source: "scheduled"`) |

## Roadmap

- Swap `gold.v_scheduled_departures` for live vehicle positions the moment
  `rapid-rail-kl` gets a realtime feed; bus categories already have one today
  and can be used to validate the realtime ingestion path early.
- Ingest `ridership_od_rapidrail_daily` into its own bronze/silver/gold path
  for the historical reliability side (delay/headway/disruption metrics).
- Move the warehouse to Supabase for production; local dev stays on DuckDB.
