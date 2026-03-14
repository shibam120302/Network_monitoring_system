"""Chaos engineering API - POST /chaos/simulate."""
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime, timedelta

from backend.schemas import ChaosSimulateRequest, ChaosSimulateResponse
from backend.chaos_engine.runner import run_chaos_simulation, FAILURE_TYPES
from database.session import get_sync_session
from database.models import ChaosSimulationRun, Node

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chaos", prefix_override="")


def get_db():
    db = get_sync_session()
    try:
        yield db
    finally:
        db.close()


@router.post("/simulate", response_model=ChaosSimulateResponse)
def chaos_simulate(req: ChaosSimulateRequest, db: Session = Depends(get_db)):
    """
    Run a chaos simulation: inject failure (packet_loss, high_latency, cpu_spike, link_failure, node_shutdown),
    verify detection and remediation, log results.
    """
    if req.failure_type not in FAILURE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"failure_type must be one of: {FAILURE_TYPES}",
        )
    try:
        run = run_chaos_simulation(
            db, req.node_id, req.failure_type, duration_seconds=req.duration_seconds or 120
        )
        return ChaosSimulateResponse(
            success=True,
            run_id=run.id,
            detection_verified=run.detection_verified,
            remediation_verified=run.remediation_verified,
            message=f"Chaos run {run.id} completed. Detection={run.detection_verified}, Remediation={run.remediation_verified}",
        )
    except Exception as e:
        logger.exception("Chaos simulate error: %s", e)
        return ChaosSimulateResponse(success=False, message=str(e))


@router.get("/runs")
def list_chaos_runs(
    node_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """List chaos simulation runs for analysis."""
    q = db.query(ChaosSimulationRun).join(Node, ChaosSimulationRun.node_id == Node.id)
    if node_id:
        q = q.filter(Node.node_id == node_id)
    runs = q.order_by(desc(ChaosSimulationRun.started_at)).limit(limit).all()
    return [
        {
            "id": r.id,
            "node_id": db.query(Node).filter(Node.id == r.node_id).first().node_id if r.node_id else None,
            "failure_type": r.failure_type,
            "started_at": r.started_at.isoformat() if r.started_at else None,
            "ended_at": r.ended_at.isoformat() if r.ended_at else None,
            "detection_verified": r.detection_verified,
            "remediation_verified": r.remediation_verified,
            "result_log": r.result_log,
        }
        for r in runs
    ]
