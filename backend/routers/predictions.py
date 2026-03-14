"""Predictive failure detection API - GET /predictions."""
import logging
from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.schemas import PredictionResponse
from backend.ml_prediction.predictor import compute_predictions
from database.session import get_sync_session
from database.models import FailurePrediction, Node

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/predictions", prefix_override="")


def get_db():
    db = get_sync_session()
    try:
        yield db
    finally:
        db.close()


@router.get("", response_model=List[PredictionResponse])
def get_predictions(
    horizon_minutes: int = Query(30, ge=10, le=60),
    recompute: bool = Query(False),
    db: Session = Depends(get_db),
):
    """
    Return failure predictions for all nodes: probability of failure in the next 10-30 minutes
    and predicted cause (e.g. cpu overload). Optionally recompute via ML.
    """
    if recompute:
        results = compute_predictions(db, horizon_minutes=horizon_minutes)
        return [PredictionResponse(**r) for r in results]

    # Return latest stored predictions
    from sqlalchemy import desc
    from datetime import datetime, timedelta
    since = datetime.utcnow() - timedelta(minutes=60)
    preds = (
        db.query(FailurePrediction, Node)
        .join(Node, FailurePrediction.node_id == Node.id)
        .filter(FailurePrediction.computed_at >= since)
        .order_by(desc(FailurePrediction.computed_at))
        .all()
    )
    # Dedupe by node_id (keep latest per node)
    seen = set()
    out = []
    for p, n in preds:
        if n.node_id in seen:
            continue
        seen.add(n.node_id)
        out.append(PredictionResponse(
            node_id=n.node_id,
            failure_probability=p.failure_probability,
            predicted_issue=p.predicted_issue,
        ))
    if not out:
        # No cached; compute once
        results = compute_predictions(db, horizon_minutes=horizon_minutes)
        return [PredictionResponse(**r) for r in results]
    return out
