"""Simulate failures by pushing synthetic metrics to trigger detection."""
from datetime import datetime
from sqlalchemy.orm import Session
import httpx

from database.models import Node
from backend.config import get_settings


def simulate_latency(db: Session, node_id: str, latency_ms: float = 300) -> bool:
    """Push a metric with high latency for node_id."""
    return _push_metric(db, node_id, latency=latency_ms)


def simulate_packet_loss(db: Session, node_id: str, packet_loss_pct: float = 15) -> bool:
    """Push a metric with high packet loss."""
    return _push_metric(db, node_id, packet_loss=packet_loss_pct)


def simulate_link_failure(db: Session, node_id: str) -> bool:
    """Push interface down."""
    return _push_metric(db, node_id, interface_status="down")


def simulate_cpu_spike(db: Session, node_id: str, cpu_pct: float = 95) -> bool:
    """Push high CPU metric."""
    return _push_metric(db, node_id, cpu_usage=cpu_pct)


def _push_metric(
    db: Session,
    node_id: str,
    latency: float = None,
    packet_loss: float = None,
    cpu_usage: float = None,
    memory_usage: float = None,
    interface_status: str = None,
) -> bool:
    """Ensure node exists and POST metric to central API (or same process)."""
    node = db.query(Node).filter(Node.node_id == node_id).first()
    if not node:
        node = Node(node_id=node_id, hostname=node_id)
        db.add(node)
        db.commit()
        db.refresh(node)

    payload = {
        "node_id": node_id,
        "timestamp": datetime.utcnow().isoformat(),
    }
    if latency is not None:
        payload["latency"] = latency
    if packet_loss is not None:
        payload["packet_loss"] = packet_loss
    if cpu_usage is not None:
        payload["cpu_usage"] = cpu_usage
    if memory_usage is not None:
        payload["memory_usage"] = memory_usage
    if interface_status is not None:
        payload["interface_status"] = interface_status

    base = get_settings().CENTRAL_API_URL
    url = f"{base.rstrip('/')}/api/v1/metrics"
    try:
        r = httpx.post(url, json=payload, timeout=5.0)
        return r.status_code == 200
    except Exception:
        return False
