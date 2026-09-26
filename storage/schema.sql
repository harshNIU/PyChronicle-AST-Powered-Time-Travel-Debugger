CREATE TABLE IF NOT EXISTS frames (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp_ns INTEGER NOT NULL,
    line_number INTEGER NOT NULL,
    event TEXT NOT NULL,
    scope TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS changes (
    frame_id INTEGER NOT NULL,
    scope TEXT NOT NULL,
    variable_name TEXT NOT NULL,
    value_json TEXT,
    operation TEXT NOT NULL,
    PRIMARY KEY (frame_id, scope, variable_name),
    FOREIGN KEY (frame_id) REFERENCES frames(id)
);

CREATE INDEX IF NOT EXISTS idx_changes_frame
ON changes(frame_id);

CREATE INDEX IF NOT EXISTS idx_changes_variable
ON changes(variable_name, frame_id);

CREATE INDEX IF NOT EXISTS idx_frames_timestamp
ON frames(timestamp_ns);

CREATE INDEX IF NOT EXISTS idx_frames_scope
ON frames(scope);

CREATE INDEX IF NOT EXISTS idx_frames_event
ON frames(event);