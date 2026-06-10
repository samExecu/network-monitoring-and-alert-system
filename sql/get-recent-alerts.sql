SELECT label, host, alert_type, message, severity, timestamp
FROM alerts
ORDER BY timestamp DESC
LIMIT ?;
