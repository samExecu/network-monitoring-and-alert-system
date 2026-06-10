SELECT rtt_ms, timestamp
FROM metrics
WHERE host = ? AND rtt_ms IS NOT NULL
ORDER BY timestamp DESC
LIMIT ?;
