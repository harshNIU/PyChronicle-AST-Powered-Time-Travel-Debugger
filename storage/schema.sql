CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp REAL NOT NULL,
    line_number INTEGER NOT NULL,
    variable_name TEXT NOT NULL,
    serialized_value TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_events_timestamp
ON events(timestamp);

CREATE INDEX IF NOT EXISTS idx_events_variable_name
ON events(variable_name);

CREATE INDEX IF NOT EXISTS idx_events_line_number
ON events(line_number);