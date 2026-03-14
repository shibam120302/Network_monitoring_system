"""Nodes API - list nodes and node details."""
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.schemas import NodeCreate, NodeResponse, NodeWithMetrics, MetricResponse
from database.session import get_sync_session
from database.models import Node, Metric

router = APIRouter(prefix="/nodes", prefix_override="")


def get_db():
    db = get_sync_session()
    try:
        yield db
    finally:
        db.close()


@router.get("", response_model=List[NodeWithMetrics])
def list_nodes(db: Session = Depends(get_db)):
    """List all nodes with latest metrics."""
    nodes = db.query(Node).filter(Node.is_active == True).all()
    result = []
    for node in nodes:
        latest = (
            db.query(Metric)
            .filter(Metric.node_id == node.id)
            .order_by(desc(Metric.timestamp))
            .first()
        )
        status = "unknown"
        if latest:
            if latest.interface_status and latest.interface_status.lower() == "down":
                status = "down"
            elif latest.latency_ms is not None and latest.latency_ms > 500:
                status = "degraded"
            else:
                status = "up"
        result.append(
            NodeWithMetrics(
                id=node.id,
                node_id=node.node_id,
                hostname=node.hostname,
                ip_address=node.ip_address,
                device_type=node.device_type,
                is_active=node.is_active,
                created_at=node.created_at,
                latest_latency=latest.latency_ms if latest else None,
                latest_packet_loss=latest.packet_loss_pct if latest else None,
                latest_cpu=latest.cpu_usage_pct if latest else None,
                status=status,
            )
        )
    return result


@router.get("/{node_id}", response_model=Optional[NodeResponse])
def get_node(node_id: str, db: Session = Depends(get_db)):
    """Get node by node_id."""
    node = db.query(Node).filter(Node.node_id == node_id).first()
    return node


@router.post("", response_model=NodeResponse)
def create_node(payload: NodeCreate, db: Session = Depends(get_db)):
    """Register a new node."""
    existing = db.query(Node).filter(Node.node_id == payload.node_id).first()
    if existing:
        return existing
    node = Node(
        node_id=payload.node_id,
        hostname=payload.hostname or payload.node_id,
        ip_address=payload.ip_address,
        device_type=payload.device_type,
        snmp_community=payload.snmp_community,
    )
    db.add(node)
    db.commit()
    db.refresh(node)
    return node


@router.get("/{node_id}/metrics", response_model=List[MetricResponse])
def get_node_metrics(
    node_id: str,
    hours: int = Query(24, ge=1, le=168),
    limit: int = Query(500, ge=1, le=2000),
    db: Session = Depends(get_db),
):
    """Get metrics for a node."""
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
