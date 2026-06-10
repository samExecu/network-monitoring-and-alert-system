CREATE TABLE IF NOT EXISTS metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    host TEXT NOT NULL,
    label TEXT NOT NULL,
    rtt_ms REAL, -- NULL means host is unreachable
    is_up INTEGER NOT NULL, -- 1 = up and 0 = down
    http_code INTEGER, -- NULL if it's not a HTTP target
    http_ms REAL, -- HTTP response time in miliseconds(ms)
    timestamp TEXT NOT NULL
);
