"""Root cause analysis API - GET /incidents/{id}/root-cause."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.schemas import RootCauseResponse
from backend.root_cause_engine.analyzer import analyze_root_cause
from database.session import get_sync_session

router = APIRouter(prefix="/incidents", prefix_override="")


def get_db():
    db = get_sync_session()
    try:
        yield db
    finally:
        db.close()


@router.get("/{incident_id}/root-cause", response_model=RootCauseResponse)
def get_incident_root_cause(incident_id: str, db: Session = Depends(get_db)):
    """
    Intelligent root cause analysis for an incident using topology, metric correlations,
    and neighboring node failures.
    """
    result = analyze_root_cause(db, incident_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return RootCauseResponse(
        incident_id=result["incident_id"],
        root_cause=result["root_cause"],
        affected_nodes=result["affected_nodes"],
        analysis_time=result.get("analysis_time"),
    )
