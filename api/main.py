"""Minimal REST API over the gold layer: lines, stations, scheduled departures.

Rail has no live vehicle-position/ETA feed yet on data.gov.my, so "next arrival"
here is the scheduled time derived from GTFS static (frequencies expansion) --
every response is explicit about that via `source: "scheduled"`.
"""
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "ingestion"))
from db import connect  # noqa: E402

MYT = timezone(timedelta(hours=8))

app = FastAPI(title="KL Rail Pulse API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_con():
    return connect()


@app.get("/api/health")
def health():
    return {"status": "ok", "server_time_myt": datetime.now(MYT).isoformat()}


@app.get("/api/lines")
def list_lines():
    con = get_con()
    rows = con.execute(
        """
        SELECT route_id, short_name, long_name, mode, color, text_color, status, num_stations
        FROM gold.dim_lines ORDER BY mode, short_name
        """
    ).fetchall()
    cols = [d[0] for d in con.description]
    con.close()
    return [dict(zip(cols, r)) for r in rows]


@app.get("/api/stations")
def list_stations(route_id: str | None = None):
    con = get_con()
    if route_id:
        rows = con.execute(
            "SELECT stop_id, name, lat, lon, mode, wheelchair_accessible, status, route_ids "
            "FROM gold.dim_stations WHERE list_contains(route_ids, ?) ORDER BY name",
            [route_id],
        ).fetchall()
    else:
        rows = con.execute(
            "SELECT stop_id, name, lat, lon, mode, wheelchair_accessible, status, route_ids "
            "FROM gold.dim_stations ORDER BY name"
        ).fetchall()
    cols = [d[0] for d in con.description]
    con.close()
    return [dict(zip(cols, r)) for r in rows]


@app.get("/api/stations/{stop_id}/departures")
def station_departures(stop_id: str, limit: int = 8):
    con = get_con()
    station = con.execute(
        "SELECT stop_id, name FROM gold.dim_stations WHERE stop_id = ?", [stop_id]
    ).fetchone()
    if not station:
        con.close()
        raise HTTPException(status_code=404, detail=f"Unknown station {stop_id}")

    now = datetime.now(MYT)
    now_seconds = now.hour * 3600 + now.minute * 60 + now.second
    weekday_col = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"][now.weekday()]

    rows = con.execute(
        f"""
        SELECT d.route_id, r.short_name, r.long_name, r.color, d.headsign, d.predicted_seconds
        FROM gold.v_scheduled_departures d
        JOIN silver.dim_calendar c ON c.service_id = d.service_id
        JOIN silver.dim_routes r ON r.route_id = d.route_id
        WHERE d.stop_id = ?
          AND c.{weekday_col} = true
          AND c.start_date <= current_date AND c.end_date >= current_date
          AND d.predicted_seconds >= ?
        ORDER BY d.predicted_seconds
        LIMIT ?
        """,
        [stop_id, now_seconds, limit],
    ).fetchall()
    con.close()

    departures = [
        {
            "route_id": r[0],
            "line_short_name": r[1],
            "line_long_name": r[2],
            "color": r[3],
            "headsign": r[4],
            "scheduled_time": f"{r[5] // 3600:02d}:{(r[5] % 3600) // 60:02d}",
            "minutes_away": round((r[5] - now_seconds) / 60),
        }
        for r in rows
    ]
    return {
        "stop_id": stop_id,
        "name": station[1],
        "source": "scheduled",
        "note": "Rail has no live vehicle-position feed on data.gov.my yet; times are derived from the published schedule, not live GPS.",
        "server_time_myt": now.strftime("%H:%M:%S"),
        "departures": departures,
    }


static_dir = Path(__file__).resolve().parent.parent / "web" / "static"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
