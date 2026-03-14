"""Email alerts via SMTP."""
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from backend.config import get_settings
from database.models import Incident, Node


def send_incident_alert(
    incident: Incident,
    node: Node,
    remediation_attempted: bool = False,
    status: str = "Pending",
) -> None:
    """Send email alert for an incident. Runs sync; call from Celery or thread in production."""
    settings = get_settings()
    if not settings.SMTP_HOST or not settings.ALERT_EMAIL_TO:
        return

    subject = "Network Incident Detected"
    body = f"""
Node: {node.node_id}
Issue: {incident.issue_type}
Severity: {incident.severity.value if hasattr(incident.severity, 'value') else incident.severity}
Time: {incident.timestamp}
Remediation Attempted: {'Yes' if remediation_attempted else 'No'}
Status: {status}
"""
    if incident.metric_snapshot:
        body += "\nMetrics at detection:\n"
        for k, v in (incident.metric_snapshot or {}).items():
            body += f"  {k}: {v}\n"

    try:
        _send_sync(settings, subject, body)
    except Exception:
        pass


def _send_sync(settings, subject: str, body: str) -> None:
    """Sync SMTP send (use aiosmtplib in async context if needed)."""
    import smtplib
    msg = MIMEMultipart()
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_FROM
    msg["To"] = settings.ALERT_EMAIL_TO
    msg.attach(MIMEText(body, "plain"))
    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as s:
        if settings.SMTP_USER and settings.SMTP_PASSWORD:
            s.starttls()
            s.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        s.sendmail(settings.SMTP_FROM, [settings.ALERT_EMAIL_TO], msg.as_string())
