PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS rack (
 id INTEGER PRIMARY KEY, code TEXT NOT NULL UNIQUE,
 capacity_units INTEGER NOT NULL CHECK(capacity_units > 0)
);
CREATE TABLE IF NOT EXISTS server (
 id INTEGER PRIMARY KEY, hostname TEXT NOT NULL UNIQUE,
 rack_id INTEGER NOT NULL REFERENCES rack(id) ON DELETE RESTRICT,
 start_unit INTEGER NOT NULL CHECK(start_unit > 0),
 units INTEGER NOT NULL CHECK(units > 0),
 watts INTEGER NOT NULL CHECK(watts >= 0),
 status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active','maintenance','retired'))
);
CREATE TABLE IF NOT EXISTS service (
 id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE,
 server_id INTEGER NOT NULL REFERENCES server(id) ON DELETE RESTRICT,
 owner TEXT NOT NULL CHECK(length(owner) > 0)
);
CREATE TABLE IF NOT EXISTS incident (
 id INTEGER PRIMARY KEY, server_id INTEGER NOT NULL REFERENCES server(id) ON DELETE RESTRICT,
 summary TEXT NOT NULL CHECK(length(summary) > 0),
 severity TEXT NOT NULL CHECK(severity IN ('low','medium','high')),
 opened_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 closed_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_server_rack ON server(rack_id);
CREATE INDEX IF NOT EXISTS idx_incident_open ON incident(server_id, closed_at);

