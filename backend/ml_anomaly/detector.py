"""Optional ML anomaly detection using Isolation Forest."""
import numpy as np
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from database.models import Metric, Node


def get_metric_matrix(db: Session, node_id: int, limit: int = 500) -> Optional[np.ndarray]:
    """Get last N metrics for node as matrix: [latency_ms, packet_loss_pct, cpu_usage_pct, memory_usage_pct]."""
    rows = (
        db.query(Metric)
        .filter(Metric.node_id == node_id)
        .order_by(desc(Metric.timestamp))
        .limit(limit)
        .all()
    )
    if len(rows) < 10:
        return None
    data = []
    for r in rows:
        data.append([
            r.latency_ms or 0,
            r.packet_loss_pct or 0,
            r.cpu_usage_pct or 0,
            r.memory_usage_pct or 0,
        ])
    return np.array(data)


def is_anomaly(db: Session, node_id: int, metric_row: List[float], contamination: float = 0.05) -> bool:
    """Train Isolation Forest on recent metrics; score metric_row; return True if anomaly."""
    try:
        from sklearn.ensemble import IsolationForest
    except ImportError:
        return False
    X = get_metric_matrix(db, node_id)
    if X is None or len(X) < 10:
        return False
    clf = IsolationForest(contamination=contamination, random_state=42)
    clf.fit(X)
    x = np.array([metric_row]).reshape(1, -1)
    pred = clf.predict(x)
    return pred[0] == -1


def check_ml_anomaly(db: Session, metric_id: int) -> bool:
    """Given a metric id, run Isolation Forest and return whether it's an anomaly."""
    metric = db.query(Metric).filter(Metric.id == metric_id).first()
    if not metric:
        return False
    row = [
        metric.latency_ms or 0,
        metric.packet_loss_pct or 0,
        metric.cpu_usage_pct or 0,
        metric.memory_usage_pct or 0,
    ]
    return is_anomaly(db, metric.node_id, row)
