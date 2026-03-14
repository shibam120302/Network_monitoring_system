"""Metrics API - receive and query metrics."""
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.schemas import MetricPayload, MetricResponse
from database.session import get_sync_session
from database.models import Node, Metric

router = APIRouter(prefix="/metrics", prefix_override="")


def get_db():
    db = get_sync_session()
    try:
        yield db
    finally:
        db.close()


@router.post("", response_model=dict)
def post_metrics(payload: MetricPayload, db: Session = Depends(get_db)):
    """Receive metrics from monitoring agents."""
    node = db.query(Node).filter(Node.node_id == payload.node_id).first()
    if not node:
        node = Node(
            node_id=payload.node_id,
            hostname=payload.node_id,
        )
        db.add(node)
        db.commit()
        db.refresh(node)

    ts = payload.timestamp or datetime.utcnow()
    metric = Metric(
        node_id=node.id,
        latency_ms=payload.latency,
        packet_loss_pct=payload.packet_loss,
        cpu_usage_pct=payload.cpu_usage,
        memory_usage_pct=payload.memory_usage,
        interface_status=payload.interface_status,
        bandwidth_usage_mbps=payload.bandwidth_usage,
        timestamp=ts,
        raw_payload=payload.model_dump(mode="json"),
    )
    db.add(metric)
    db.commit()

    # Trigger anomaly detection (async via Celery in production)
    from backend.incident_engine.detector import check_metrics_and_create_incident
    try:
        check_metrics_and_create_incident(db, metric, node)
    except Exception:
        pass
    db.commit()

    return {"status": "ok", "metric_id": metric.id}


@router.get("/nodes/{node_id}/history", response_model=List[MetricResponse])
def get_node_metrics(
    node_id: str,
    hours: int = Query(24, ge=1, le=168),
    limit: int = Query(500, ge=1, le=2000),
    db: Session = Depends(get_db),
):
    """Get metric history for a node (by node_id string e.g. node-23)."""
    node = db.query(Node).filter(Node.node_id == node_id).first()
    if not node:
        return []
    since = datetime.utcnow() - timedelta(hours=hours)
    rows = (
        db.query(Metric)
        .filter(Metric.node_id == node.id, Metric.timestamp >= since)
        .order_by(desc(Metric.timestamp))
        .limit(limit)
        .all()
    )
    return rows
