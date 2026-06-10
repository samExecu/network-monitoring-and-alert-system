SELECT host, label, rtt_ms, is_up, http_code, http_ms, timestamp
FROM metrics
ORDER BY timestamp DESC
LIMIT ?;
