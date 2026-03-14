"""Rule-based and optional ML anomaly detection."""
import uuid
from datetime import datetime
from sqlalchemy.orm import Session

from backend.config import get_settings
from database.models import (
    Node,
    Metric,
    Incident,
    IncidentTimelineEvent,
    IncidentStatus,
    IncidentSeverity,
)


def check_metrics_and_create_incident(db: Session, metric: Metric, node: Node) -> Incident | None:
    """Rule-based: check metric against thresholds; create incident and timeline; trigger remediation & alert."""
    settings = get_settings()
    issue_type = None
    severity = IncidentSeverity.MEDIUM

    # Node unreachable (no recent valid metric or all null and we treat as unreachable from agent)
    if metric.latency_ms is None and metric.packet_loss_pct is None and metric.cpu_usage_pct is None:
        # Could be agent failed to collect
        issue_type = "node_unreachable"
        severity = IncidentSeverity.CRITICAL
    elif metric.latency_ms is not None and metric.latency_ms > settings.THRESHOLD_LATENCY_MS:
        issue_type = "high_latency"
        severity = IncidentSeverity.HIGH if metric.latency_ms > 200 else IncidentSeverity.MEDIUM
    elif metric.packet_loss_pct is not None and metric.packet_loss_pct > settings.THRESHOLD_PACKET_LOSS_PCT:
        issue_type = "high_packet_loss"
        severity = IncidentSeverity.HIGH if metric.packet_loss_pct > 10 else IncidentSeverity.MEDIUM
    elif metric.cpu_usage_pct is not None and metric.cpu_usage_pct > settings.THRESHOLD_CPU_PCT:
        issue_type = "high_cpu"
        severity = IncidentSeverity.MEDIUM
    elif metric.interface_status and str(metric.interface_status).lower() == "down":
        issue_type = "interface_down"
        severity = IncidentSeverity.HIGH
    elif metric.memory_usage_pct is not None and metric.memory_usage_pct > getattr(settings, "THRESHOLD_MEMORY_PCT", 90):
        issue_type = "high_memory"
        severity = IncidentSeverity.MEDIUM

    if not issue_type:
        return None

    # Avoid duplicate open incident for same issue type on same node
    existing = (
        db.query(Incident)
        .filter(
            Incident.node_id == node.id,
            Incident.issue_type == issue_type,
            Incident.status.in_([IncidentStatus.OPEN.value, IncidentStatus.INVESTIGATING.value, IncidentStatus.REMEDIATING.value]),
        )
        .first()
    )
    if existing:
        return None

    incident_id = f"inc-{uuid.uuid4().hex[:12]}"
    incident = Incident(
        incident_id=incident_id,
        node_id=node.id,
        issue_type=issue_type,
        severity=severity,
        status=IncidentStatus.OPEN,
        timestamp=metric.timestamp,
        description=f"{issue_type} on {node.node_id}",
        metric_snapshot={
            "latency_ms": metric.latency_ms,
            "packet_loss_pct": metric.packet_loss_pct,
            "cpu_usage_pct": metric.cpu_usage_pct,
            "memory_usage_pct": metric.memory_usage_pct,
            "interface_status": metric.interface_status,
        },
    )
    db.add(incident)
    db.flush()

    # Timeline: detected, created
    now = datetime.utcnow()
    for event_type, msg in [
        ("detected", f"{issue_type} detected"),
        ("created", f"Incident {incident_id} created"),
    ]:
        db.add(
            IncidentTimelineEvent(
                incident_id=incident.id,
                event_time=now,
                event_type=event_type,
                message=msg,
            )
        )
    db.flush()

    # Trigger remediation (async in production via Celery)
    try:
        from backend.remediation_engine.runner import trigger_remediation_for_incident
        trigger_remediation_for_incident(db, incident)
    except Exception:
        pass

    # Trigger alert
    try:
        from backend.alerts.service import send_incident_alert
        send_incident_alert(incident, node, remediation_attempted=False, status="Pending")
    except Exception:
        pass

    return incident
