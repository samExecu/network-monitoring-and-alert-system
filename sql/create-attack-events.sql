CREATE TABLE IF NOT EXISTS attack_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    host TEXT NOT NULL,
    attack_type TEXT NOT NULL, -- FLOOD, PORTSCAN, ANOMALY, etc.
    description TEXT NOT NULL,
    severity TEXT NOT NULL,
    timestamp TEXT NOT NULL
);
