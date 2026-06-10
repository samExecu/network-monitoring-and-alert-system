SELECT host, label, rtt_ms, is_up, http_code, timestamp
FROM metrics
WHERE id IN (
    SELECT MAX(id) FROM metrics GROUP BY host
)
ORDER BY label;
