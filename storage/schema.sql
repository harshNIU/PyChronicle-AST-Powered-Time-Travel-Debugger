CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp REAL NOT NULL,
    line_number INTEGER NOT NULL,
    variable_name TEXT NOT NULL,
    serialized_value TEXT NOT NULL
);