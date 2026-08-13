-- Gold: business-ready serving layer consumed directly by the API.
-- v_scheduled_departures expands frequencies.txt (headway-based service) into
-- individual predicted departure times per stop, since Prasarana rail publishes
-- template trips + headways rather than one row per physical run. There is no
-- live vehicle-position feed for rail yet (see README), so this scheduled
-- expansion is what "next arrival" means until that lands.

CREATE OR REPLACE TABLE gold.dim_lines AS
SELECT
    r.route_id,
    r.short_name,
    r.long_name,
    r.mode,
    r.color,
    r.text_color,
    r.status,
    count(DISTINCT st.stop_id) AS num_stations
FROM silver.dim_routes r
LEFT JOIN silver.fact_stop_times st ON st.route_id = r.short_name
GROUP BY r.route_id, r.short_name, r.long_name, r.mode, r.color, r.text_color, r.status;

CREATE OR REPLACE TABLE gold.dim_stations AS
SELECT
    s.stop_id,
    s.name,
    s.lat,
    s.lon,
    s.mode,
    s.wheelchair_accessible,
    s.status,
    list(DISTINCT s.primary_route_id) AS route_ids
FROM silver.dim_stops s
GROUP BY s.stop_id, s.name, s.lat, s.lon, s.mode, s.wheelchair_accessible, s.status;

CREATE OR REPLACE VIEW gold.v_scheduled_departures AS
WITH trip_origin AS (
    SELECT trip_id, min(arrival_seconds) AS origin_seconds
    FROM silver.fact_stop_times
    GROUP BY trip_id
),
stop_offsets AS (
    SELECT st.trip_id, st.stop_id, st.stop_sequence, st.route_id, st.direction_id,
           st.arrival_seconds - o.origin_seconds AS offset_seconds
    FROM silver.fact_stop_times st
    JOIN trip_origin o USING (trip_id)
),
expanded_runs AS (
    SELECT
        f.trip_id,
        f.start_seconds + gs.n * f.headway_secs AS run_origin_seconds
    FROM silver.fact_frequencies f,
         generate_series(0, CAST(floor((f.end_seconds - f.start_seconds) / f.headway_secs) AS BIGINT)) AS gs(n)
)
SELECT
    t.trip_id,
    t.route_id,
    t.service_id,
    t.direction_id,
    t.headsign,
    so.stop_id,
    so.stop_sequence,
    er.run_origin_seconds + so.offset_seconds AS predicted_seconds
FROM expanded_runs er
JOIN silver.dim_trips t ON t.trip_id = er.trip_id
JOIN stop_offsets so ON so.trip_id = er.trip_id;
