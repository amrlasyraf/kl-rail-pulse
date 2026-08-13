-- Bronze: raw GTFS static rows as landed, minimally typed, one batch per ingestion run.
-- Every table carries the same lineage columns so silver can always pick the latest batch.

CREATE TABLE IF NOT EXISTS bronze.gtfs_agency (
    agency_id VARCHAR, agency_name VARCHAR, agency_url VARCHAR,
    agency_timezone VARCHAR, agency_phone VARCHAR, agency_lang VARCHAR,
    _category VARCHAR, _batch_id VARCHAR, _loaded_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bronze.gtfs_routes (
    route_id VARCHAR, agency_id VARCHAR, route_short_name VARCHAR, route_long_name VARCHAR,
    route_desc VARCHAR, route_type VARCHAR, route_color VARCHAR, route_text_color VARCHAR,
    category VARCHAR, status VARCHAR,
    _category VARCHAR, _batch_id VARCHAR, _loaded_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bronze.gtfs_stops (
    stop_id VARCHAR, stop_name VARCHAR, stop_lat VARCHAR, stop_lon VARCHAR,
    category VARCHAR, route_id VARCHAR, geometry VARCHAR, isOKU VARCHAR, status VARCHAR, search VARCHAR,
    _category VARCHAR, _batch_id VARCHAR, _loaded_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bronze.gtfs_trips (
    route_id VARCHAR, service_id VARCHAR, trip_id VARCHAR, trip_headsign VARCHAR,
    direction_id VARCHAR, shape_id VARCHAR,
    _category VARCHAR, _batch_id VARCHAR, _loaded_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bronze.gtfs_stop_times (
    route_id VARCHAR, direction_id VARCHAR, trip_id VARCHAR,
    arrival_time VARCHAR, departure_time VARCHAR, stop_id VARCHAR, stop_sequence VARCHAR,
    _category VARCHAR, _batch_id VARCHAR, _loaded_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bronze.gtfs_calendar (
    service_id VARCHAR, monday VARCHAR, tuesday VARCHAR, wednesday VARCHAR, thursday VARCHAR,
    friday VARCHAR, saturday VARCHAR, sunday VARCHAR, start_date VARCHAR, end_date VARCHAR,
    _category VARCHAR, _batch_id VARCHAR, _loaded_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bronze.gtfs_frequencies (
    trip_id VARCHAR, start_time VARCHAR, end_time VARCHAR, headway_secs VARCHAR,
    _category VARCHAR, _batch_id VARCHAR, _loaded_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bronze.gtfs_shapes (
    shape_id VARCHAR, shape_pt_lon VARCHAR, shape_pt_lat VARCHAR, shape_pt_sequence VARCHAR,
    _category VARCHAR, _batch_id VARCHAR, _loaded_at TIMESTAMP
);
