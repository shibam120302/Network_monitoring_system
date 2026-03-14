"""SLA metrics API - uptime %, MTTR, MTBF."""
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from backend.schemas import SLAResponse
from database.session import get_sync_session
from database.models import Node, Incident, SLAMetrics

router = APIRouter(prefix="/sla", prefix_override="")


def get_db():
    db = get_sync_session()
    try:
        yield db
    finally:
        db.close()


def _compute_sla(db: Session, node_id: Optional[int], period_hours: int):
    end = datetime.utcnow()
    start = end - timedelta(hours=period_hours)
    incidents = (
        db.query(Incident)
        .filter(and_(Incident.timestamp >= start, Incident.timestamp <= end))
    )
    if node_id is not None:
        incidents = incidents.filter(Incident.node_id == node_id)
    incidents = incidents.all()

    total_minutes = period_hours * 60.0
    downtime_minutes = 0.0
    recovery_times = []
    gap_times = []
    prev_end = start

    for inc in sorted(incidents, key=lambda x: x.timestamp):
        res_at = inc.resolved_at or end
        dur = (res_at - inc.timestamp).total_seconds() / 60
        downtime_minutes += dur
        recovery_times.append(dur)
        gap_times.append((inc.timestamp - prev_end).total_seconds() / 60)
        prev_end = res_at

    uptime_pct = max(0, 100 - (downtime_minutes / total_minutes * 100)) if total_minutes else 100
    mttr = sum(recovery_times) / len(recovery_times) if recovery_times else None
    mtbf = sum(gap_times) / len(gap_times) if gap_times else None

    return {
        "uptime_pct": round(uptime_pct, 2),
        "mttr_minutes": round(mttr, 2) if mttr is not None else None,
        "mtbf_minutes": round(mtbf, 2) if mtbf is not None else None,
        "incident_count": len(incidents),
        "period_start": start,
        "period_end": end,
    }


@router.get("", response_model=List[SLAResponse])
def get_sla(
    node_id: Optional[str] = Query(None),
    hours: int = Query(24, ge=1, le=720),
    db: Session = Depends(get_db),
):
    """Get SLA metrics: uptime %, MTTR, MTBF. Optional node_id for per-node SLA."""
    node_pk = None
    node_node_id = None
    if node_id:
        node = db.query(Node).filter(Node.node_id == node_id).first()
        if node:
            node_pk = node.id
            node_node_id = node.node_id

    data = _compute_sla(db, node_pk, hours)
    return [
        SLAResponse(
            node_id=node_pk,
            node_node_id=node_node_id,
            period_start=data["period_start"],
            period_end=data["period_end"],
            uptime_pct=data["uptime_pct"],
            mttr_minutes=data["mttr_minutes"],
            mtbf_minutes=data["mtbf_minutes"],
            incident_count=data["incident_count"],
        )
    ]
