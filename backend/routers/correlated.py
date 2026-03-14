"""Event correlation API - GET /incidents/correlated."""
from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from backend.schemas import CorrelatedGroupResponse
from backend.event_correlation.correlator import get_correlated_groups, run_correlation
from database.session import get_sync_session

router = APIRouter(prefix="/incidents", prefix_override="")


def get_db():
    db = get_sync_session()
    try:
        yield db
    finally:
        db.close()


@router.get("/correlated", response_model=List[CorrelatedGroupResponse])
def get_correlated_incidents(
    limit: int = Query(50, ge=1, le=200),
    run_now: bool = Query(False),
    hours: int = Query(24, ge=1, le=168),
    db: Session = Depends(get_db),
):
    """
    Return correlated incident groups (alerts grouped by time proximity, topology, metric similarity).
    Optionally run correlation now on last N hours.
    """
    if run_now:
        since = datetime.utcnow() - timedelta(hours=hours)
        run_correlation(db, since=since)
    raw = get_correlated_groups(db, limit=limit)
    return [
        CorrelatedGroupResponse(
            group_id=g["group_id"],
            root_cause_summary=g["root_cause_summary"],
            created_at=g["created_at"],
            incident_ids=g["incident_ids"],
            affected_nodes=g["affected_nodes"],
        )
        for g in raw
    ]
