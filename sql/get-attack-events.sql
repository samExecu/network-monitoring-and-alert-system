SELECT host, attack_type, description, severity, timestamp
FROM attack_events
ORDER BY timestamp DESC
LIMIT ?;
