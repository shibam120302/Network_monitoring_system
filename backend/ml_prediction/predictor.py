"""
Predictive failure detection: train on historical metrics and predict probability of node failure
within the next 10-30 minutes. Uses Isolation Forest / Random Forest.
"""
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import desc

from database.models import Node, Metric, Incident, FailurePrediction

logger = logging.getLogger(__name__)

# Feature columns used for prediction
FEATURE_COLS = ["latency_ms", "packet_loss_pct", "cpu_usage_pct", "memory_usage_pct", "bandwidth_usage_mbps"]
HORIZON_MINUTES = 30
MIN_SAMPLES_TRAIN = 50
MODEL_VERSION = "v1-isolation-forest"


def _get_metric_matrix_and_labels(
    db: Session, node_pk: int, lookback_hours: int = 24
) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
    """
    For each metric row in the last lookback_hours, build feature vector and label:
    label=1 if an incident occurred on this node within HORIZON_MINUTES after the metric timestamp.
    """
    since = datetime.utcnow() - timedelta(hours=lookback_hours)
    metrics = (
        db.query(Metric)
        .filter(Metric.node_id == node_pk, Metric.timestamp >= since)
        .order_by(Metric.timestamp)
        .all()
    )
    if len(metrics) < MIN_SAMPLES_TRAIN:
        return None, None

    incidents_in_window = (
        db.query(Incident)
        .filter(Incident.node_id == node_pk, Incident.timestamp >= since)
        .all()
    )
    incident_times = {inc.timestamp for inc in incidents_in_window}

    X_list = []
    y_list = []
    for m in metrics:
        vec = [
            m.latency_ms if m.latency_ms is not None else 0.0,
            m.packet_loss_pct if m.packet_loss_pct is not None else 0.0,
            m.cpu_usage_pct if m.cpu_usage_pct is not None else 0.0,
            m.memory_usage_pct if m.memory_usage_pct is not None else 0.0,
            m.bandwidth_usage_mbps if m.bandwidth_usage_mbps is not None else 0.0,
        ]
        X_list.append(vec)
        # Label: 1 if any incident in [m.timestamp, m.timestamp + HORIZON]
        end = m.timestamp + timedelta(minutes=HORIZON_MINUTES)
        label = 1 if any(inc_ts >= m.timestamp and inc_ts <= end for inc_ts in incident_times) else 0
        y_list.append(label)

    X = np.array(X_list)
    y = np.array(y_list)
    if np.sum(y) == 0 and np.sum(1 - y) < MIN_SAMPLES_TRAIN:
        return None, None
    return X, y


def _predict_issue_from_features(vec: np.ndarray) -> str:
    """Heuristic: which metric is most anomalous (highest relative value) to name predicted issue."""
    # Normalize by typical max (rough thresholds)
    maxes = np.array([200.0, 20.0, 100.0, 100.0, 1000.0])
    normalized = np.clip(vec / maxes, 0, 1)
    names = ["latency", "packet loss", "cpu overload", "memory pressure", "bandwidth congestion"]
    i = int(np.argmax(normalized))
    return names[i]


def compute_predictions(db: Session, horizon_minutes: int = 30) -> List[dict]:
    """
    For each active node with enough history, train a model (or use Isolation Forest anomaly score),
    predict failure probability for the next horizon_minutes, and optionally persist to FailurePrediction.
    Returns list of { node_id, failure_probability, predicted_issue }.
    """
    try:
        from sklearn.ensemble import IsolationForest
        from sklearn.preprocessing import StandardScaler
    except ImportError:
        logger.warning("sklearn not available; returning empty predictions")
        return []

    nodes = db.query(Node).filter(Node.is_active == True).all()
    results = []
    now = datetime.utcnow()

    for node in nodes:
        X, y = _get_metric_matrix_and_labels(db, node.id)
        if X is None or len(X) < MIN_SAMPLES_TRAIN:
            continue

        # Use Isolation Forest: -1 = anomaly. We want "probability of failure" so we use
        # decision_function (lower = more anomalous) mapped to [0,1], or train a small Random Forest
        # for binary classification if we have enough positive labels.
        failure_prob = 0.0
        predicted_issue = "unknown"

        if np.sum(y) >= 5:
            # Enough failures: train Random Forest for probability
            try:
                from sklearn.ensemble import RandomForestClassifier
                from sklearn.model_selection import train_test_split
                scaler = StandardScaler()
                Xs = scaler.fit_transform(X)
                X_train, X_test, y_train, _ = train_test_split(Xs, y, test_size=0.2, random_state=42)
                clf = RandomForestClassifier(n_estimators=50, random_state=42)
                clf.fit(X_train, y_train)
                # Predict on latest window (last 5 metrics)
                latest = X[-5:] if len(X) >= 5 else X[-1:]
                latest_scaled = scaler.transform(latest)
                proba = clf.predict_proba(latest_scaled)
                failure_prob = float(proba[:, 1].mean()) if proba.shape[1] > 1 else 0.0
                predicted_issue = _predict_issue_from_features(X[-1])
            except Exception as e:
                logger.debug("RF failed for node %s: %s", node.node_id, e)
                # Fallback to Isolation Forest anomaly score
                clf = IsolationForest(contamination=0.1, random_state=42)
                clf.fit(X)
                score = clf.decision_function(X[-1:])
                # decision_function: more negative = more anomalous; map to [0,1]
                failure_prob = float(np.clip(0.5 - score[0] / 2.0, 0, 1))
                predicted_issue = _predict_issue_from_features(X[-1])
        else:
            # Few or no failures: use Isolation Forest anomaly score only
            clf = IsolationForest(contamination=0.1, random_state=42)
            clf.fit(X)
            score = clf.decision_function(X[-1:])
            failure_prob = float(np.clip(0.5 - score[0] / 2.0, 0, 1))
            predicted_issue = _predict_issue_from_features(X[-1])

        results.append({
            "node_id": node.node_id,
            "failure_probability": round(failure_prob, 4),
            "predicted_issue": predicted_issue,
        })

        # Persist
        fp = FailurePrediction(
            node_id=node.id,
            failure_probability=failure_prob,
            predicted_issue=predicted_issue,
            horizon_minutes=horizon_minutes,
            computed_at=now,
            model_version=MODEL_VERSION,
        )
        db.add(fp)

    db.commit()
    return results
