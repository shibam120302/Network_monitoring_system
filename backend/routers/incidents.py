"""Incidents API and timeline."""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.schemas import IncidentResponse, IncidentDetailResponse, IncidentTimelineEventResponse
from database.session import get_sync_session
from database.models import Incident, IncidentTimelineEvent, Node

router = APIRouter(prefix="/incidents", prefix_override="")


def get_db():
    db = get_sync_session()
    try:
        yield db
    finally:
        db.close()


@router.get("", response_model=List[IncidentResponse])
def list_incidents(
    status: Optional[str] = Query(None),
    node_id: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """List incidents with optional filters."""
    q = db.query(Incident, Node).join(Node, Incident.node_id == Node.id)
    if status:
        q = q.filter(Incident.status == status)
    if node_id:
        q = q.filter(Node.node_id == node_id)
    q = q.order_by(desc(Incident.timestamp)).limit(limit)
    rows = q.all()
    return [
        IncidentResponse(
            id=inc.id,
            incident_id=inc.incident_id,
            node_id=inc.node_id,
            node_node_id=node.node_id,
            issue_type=inc.issue_type,
            severity=inc.severity.value if hasattr(inc.severity, "value") else str(inc.severity),
            status=inc.status.value if hasattr(inc.status, "value") else str(inc.status),
            timestamp=inc.timestamp,
            resolved_at=inc.resolved_at,
            root_cause=inc.root_cause,
            description=inc.description,
        )
        for inc, node in rows
    ]


@router.get("/{incident_id}", response_model=Optional[IncidentDetailResponse])
def get_incident(incident_id: str, db: Session = Depends(get_db)):
    """Get incident by incident_id (e.g. inc-abc123) with timeline."""
    incident = db.query(Incident).filter(Incident.incident_id == incident_id).first()
    if not incident:
        return None
    node = db.query(Node).filter(Node.id == incident.node_id).first()
    timeline = (
        db.query(IncidentTimelineEvent)
        .filter(IncidentTimelineEvent.incident_id == incident.id)
        .order_by(IncidentTimelineEvent.event_time)
        .all()
    )
    return IncidentDetailResponse(
        id=incident.id,
        incident_id=incident.incident_id,
        node_id=incident.node_id,
        issue_type=incident.issue_type,
        severity=incident.severity.value if hasattr(incident.severity, "value") else str(incident.severity),
        status=incident.status.value if hasattr(incident.status, "value") else str(incident.status),
        timestamp=incident.timestamp,
        resolved_at=incident.resolved_at,
        root_cause=incident.root_cause,
        description=incident.description,
        timeline=[IncidentTimelineEventResponse(id=e.id, event_time=e.event_time, event_type=e.event_type, message=e.message) for e in timeline],
        node_node_id=node.node_id if node else None,
    )
