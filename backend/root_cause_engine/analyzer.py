"""
Intelligent root cause analysis: use topology graph, metric correlations, and neighboring node
failures to determine the most likely root cause of an incident.
"""
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Set
from sqlalchemy.orm import Session
from sqlalchemy import and_

from database.models import Node, Incident, Metric, TopologyLink

logger = logging.getLogger(__name__)

# Time window to consider "same time" incidents (minutes)
PROXIMITY_MINUTES = 10


def _get_neighbor_node_ids(db: Session, node_pk: int) -> Set[int]:
    """Get all node IDs that are directly linked to this node in topology."""
    links = db.query(TopologyLink).filter(
        (TopologyLink.source_node_id == node_pk) | (TopologyLink.target_node_id == node_pk)
    ).all()
    out = set()
    for link in links:
        out.add(link.source_node_id)
        out.add(link.target_node_id)
    out.discard(node_pk)
    return out


def _get_upstream_common_ancestor(db: Session, node_pks: List[int]) -> Optional[str]:
    """
    If multiple nodes share a common neighbor (e.g. same switch), return a label for that.
    We don't have explicit 'switch' - treat common neighbor as upstream aggregation point.
    """
    if len(node_pks) < 2:
        return None
    # For each node, get neighbors; find intersection of neighbors (common upstream)
    neighbor_sets = []
    for pk in node_pks:
        neighbor_sets.append(_get_neighbor_node_ids(db, pk))
    common = set.intersection(*neighbor_sets) if neighbor_sets else set()
    if not common:
        return None
    # Get one common node's node_id for label
    first = db.query(Node).filter(Node.id == list(common)[0]).first()
    return f"upstream node {first.node_id}" if first else None


def analyze_root_cause(db: Session, incident_id: str) -> dict:
    """
    Analyze incident and return root cause summary and affected nodes.
    Logic:
    - If multiple nodes show latency and share same upstream (topology) -> root cause = upstream/switch.
    - If single node, use metric snapshot and issue_type to infer cause.
    """
    incident = db.query(Incident).filter(Incident.incident_id == incident_id).first()
    if not incident:
        return {"error": "Incident not found", "incident_id": incident_id}

    node = db.query(Node).filter(Node.id == incident.node_id).first()
    if not node:
        return {"incident_id": incident_id, "root_cause": "Unknown", "affected_nodes": []}

    start = incident.timestamp - timedelta(minutes=PROXIMITY_MINUTES)
    end = incident.timestamp + timedelta(minutes=PROXIMITY_MINUTES)

    # Find incidents on same node or neighboring nodes in time window
    neighbor_pks = _get_neighbor_node_ids(db, incident.node_id)
    all_related_pks = {incident.node_id} | neighbor_pks

    related_incidents = (
        db.query(Incident)
        .filter(
            Incident.node_id.in_(all_related_pks),
            Incident.timestamp >= start,
            Incident.timestamp <= end,
        )
        .all()
    )

    affected_node_pks = list({i.node_id for i in related_incidents})
    affected_nodes = []
    for pk in affected_node_pks:
        n = db.query(Node).filter(Node.id == pk).first()
        if n:
            affected_nodes.append(n.node_id)

    # Determine root cause
    root_cause = incident.root_cause
    if not root_cause and len(affected_node_pks) >= 2:
        upstream = _get_upstream_common_ancestor(db, affected_node_pks)
        if upstream:
            root_cause = f"Congestion or failure at {upstream}"
        else:
            root_cause = "Multiple nodes affected in same time window (possible network-wide issue)"
    if not root_cause:
        # Single node: infer from issue_type and metrics
        snapshot = incident.metric_snapshot or {}
        it = incident.issue_type
        if it == "high_latency":
            root_cause = f"Latency spike (measured: {snapshot.get('latency_ms', 'N/A')} ms)"
        elif it == "high_packet_loss":
            root_cause = f"Packet loss (measured: {snapshot.get('packet_loss_pct', 'N/A')}%)"
        elif it == "high_cpu":
            root_cause = "CPU overload"
        elif it == "interface_down":
            root_cause = "Network interface down"
        elif it == "node_unreachable":
            root_cause = "Node unreachable (agent or connectivity)"
        else:
            root_cause = incident.description or f"Issue: {it}"

    return {
        "incident_id": incident_id,
        "root_cause": root_cause,
        "affected_nodes": affected_nodes,
        "analysis_time": datetime.utcnow().isoformat(),
    }
