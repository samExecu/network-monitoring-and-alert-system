SELECT
    label,
    host,
    COUNT(*) AS total,
    SUM(is_up) AS up_count,
    ROUND(AVG(CASE WHEN rtt_ms IS NOT NULL THEN rtt_ms END), 1) AS avg_rtt,
    MAX(rtt_ms) AS max_rtt,
    ROUND(AVG(CASE WHEN http_ms IS NOT NULL THEN http_ms END), 1) AS avg_http_ms,
    MAX(is_up) AS current_up,
    MAX(timestamp) AS last_seen
FROM metrics
WHERE timestamp > datetime('now', '-24 hours')
GROUP BY host
ORDER BY label;
