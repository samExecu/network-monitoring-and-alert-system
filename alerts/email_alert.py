"""
Setup (Gmail App Password):
1. Go to your Google Account > Security
2. Enable 2-Step Verification (if not already on)
3. Search for "App Passwords" in your Google account
4. Create one for "Mail" — you get a 16-character password
5. Put that password as EMAIL_PASSWORD in your .env file
    (You cannot use your regular Gmail password here)
"""

import smtplib
import ssl
import config
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

# Map severity levels to colors for the HTML email
_SEVERITY_COLOR = {
    "CRITICAL": "#dc2626",
    "WARNING": "#d97706",
    "INFO": "#2563eb",
    "RECOVERY": "#16a34a",
}

# Map severity levels
_SEVERITY_LABEL = {
    "CRITICAL": "CRITICAL",
    "WARNING": "WARNING",
    "INFO": "INFO",
    "RECOVERY": "RECOVERY",
}


def send_email_alert(label: str, host: str, alert_type: str,
                      message: str, severity: str = "WARNING") -> None:
    """
    Send an HTML email alert via Gmail.
    Silently skips if email credentials are not set in .env.
    """
    if not all([config.EMAIL_SENDER, config.EMAIL_PASSWORD, config.EMAIL_RECIPIENT]):
        return

    color = _SEVERITY_COLOR.get(severity, "#d97706")
    severity_text = _SEVERITY_LABEL.get(severity, "WARNING")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # create the email message
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"[NetMon {severity_text}] {label} — {alert_type}"
    msg["From"] = config.EMAIL_SENDER
    msg["To"] = config.EMAIL_RECIPIENT

    # Fallback as plain text, if it fails
    text = (
        f"NETWORK ALERT\n"
        f"{'='*40}\n"
        f"Host: {label} ({host})\n"
        f"Alert: {alert_type}\n"
        f"Severity: {severity_text}\n"
        f"Message: {message}\n"
        f"Time: {now}\n"
    )

    # HTML
    html = f"""
    <!DOCTYPE html>
    <html>
    <body style="font-family:Arial,sans-serif;background:#f8fafc;padding:30px;">
    <div style="max-width:520px;margin:auto;background:#fff;border-radius:8px;
    border-top:4px solid {color};padding:24px;box-shadow:0 2px 8px rgba(0,0,0,.1);">
        <h2 style="margin:0 0 16px;color:{color};">{alert_type}</h2>
        <table style="width:100%;border-collapse:collapse;">
            <tr style="background:#f1f5f9;">
                <td style="padding:8px 12px;font-weight:bold;color:#475569;">Host</td>
                <td style="padding:8px 12px;font-family:monospace;">{label} ({host})</td>
            </tr>
            <tr>
                <td style="padding:8px 12px;font-weight:bold;color:#475569;">Severity</td>
                <td style="padding:8px 12px;color:{color};font-weight:bold;">{severity_text}</td>
            </tr>
            <tr style="background:#f1f5f9;">
                <td style="padding:8px 12px;font-weight:bold;color:#475569;">Message</td>
                <td style="padding:8px 12px;">{message}</td>
            </tr>
            <tr>
                <td style="padding:8px 12px;font-weight:bold;color:#475569;">Time</td>
                <td style="padding:8px 12px;color:#64748b;">{now}</td>
            </tr>
        </table>
        <p style="margin:20px 0 0;font-size:12px;color:#94a3b8;">
            Sent by NetMon — Network Monitoring & Alert System
        </p>
    </div>
    </body>
    </html>
    """

    # Attach both plain text and the HTML versions
    msg.attach(MIMEText(text, "plain"))
    msg.attach(MIMEText(html, "html"))

    # Send mail via Gmail SMTP
    try:
        ctx = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ctx) as server:
            server.login(config.EMAIL_SENDER, config.EMAIL_PASSWORD)
            server.sendmail(config.EMAIL_SENDER, config.EMAIL_RECIPIENT, msg.as_string())
    except Exception as e:
        print(f"[EMAIL ERROR] {e}")

"""
Test Block
"""
if __name__ == "__main__":
    print("[TEST] Sending sample email alert...")

    # Example values for testing
    test_label = "Localhost"
    test_host = "127.0.0.1"
    test_alert_type = "DOWN"
    test_message = "Host unreachable"
    test_severity = "CRITICAL"

    # Attempt to send a test email
    send_email_alert(
        label=test_label,
        host=test_host,
        alert_type=test_alert_type,
        message=test_message,
        severity=test_severity
    )

    print("[TEST] Done. Check your inbox (or console for errors).")