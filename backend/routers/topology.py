"""Topology API - network graph."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.schemas import TopologyResponse, TopologyNode, TopologyEdge
from backend.topology.builder import build_topology
from database.session import get_sync_session

router = APIRouter(prefix="/topology", prefix_override="")


def get_db():
    db = get_sync_session()
    try:
        yield db
    finally:
        db.close()


@router.get("", response_model=TopologyResponse)
def get_topology(db: Session = Depends(get_db)):
    """Get network topology (nodes + edges) with status and link health."""
    data = build_topology(db)
    return TopologyResponse(
        nodes=[TopologyNode(**n) for n in data["nodes"]],
        edges=[TopologyEdge(**e) for e in data["edges"]],
        graph_json=data.get("graph_json"),
    )
