"""
Event correlation: group related alerts/incidents into a single root incident to reduce noise.
Correlation factors: time proximity, topology relationship, metric similarity.
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from database.models import Node, Incident, TopologyLink, IncidentCorrelationGroup, CorrelatedIncident

logger = logging.getLogger(__name__)

TIME_PROXIMITY_SEC = 300  # 5 minutes
METRIC_SIMILARITY_ISSUE = True  # same issue_type = similar


def _neighbors_set(db: Session, node_pk: int) -> set:
    links = db.query(TopologyLink).filter(
        (TopologyLink.source_node_id == node_pk) | (TopologyLink.target_node_id == node_pk)
    ).all()
    out = set()
    for link in links:
        out.add(link.source_node_id)
        out.add(link.target_node_id)
    out.discard(node_pk)
    return out


def run_correlation(db: Session, since: datetime = None) -> List[dict]:
    """
    Find open/recent incidents, group by time proximity + topology + issue similarity,
    create IncidentCorrelationGroup and CorrelatedIncident records.
    Returns list of correlation groups with summary and member incident_ids.
    """
    since = since or (datetime.utcnow() - timedelta(hours=24))
    incidents = (
        db.query(Incident)
        .filter(Incident.timestamp >= since)
        .order_by(Incident.timestamp)
        .all()
    )
    if len(incidents) < 2:
        return []

    # Build adjacency: incident_i and incident_j are related if
    # - time within TIME_PROXIMITY_SEC
    # - same issue_type or topology neighbors
    n = len(incidents)
    used = [False] * n
    groups_out = []

    for i in range(n):
        if used[i]:
            continue
        inc_i = incidents[i]
        node_i = inc_i.node_id
        neighbors_i = _neighbors_set(db, node_i)
        group_incidents = [inc_i]
        used[i] = True

        for j in range(i + 1, n):
            if used[j]:
                continue
            inc_j = incidents[j]
            if abs((inc_j.timestamp - inc_i.timestamp).total_seconds()) > TIME_PROXIMITY_SEC:
                continue
            if inc_j.node_id == node_i or inc_j.node_id in neighbors_i:
                if not METRIC_SIMILARITY_ISSUE or inc_i.issue_type == inc_j.issue_type:
                    group_incidents.append(inc_j)
                    used[j] = True

        if len(group_incidents) >= 2:
            # Create correlation group
            summary = f"{group_incidents[0].issue_type} across {len(group_incidents)} nodes (topology + time correlated)"
            grp = IncidentCorrelationGroup(
                root_cause_summary=summary,
                created_at=datetime.utcnow(),
                metadata_={
                    "time_proximity_sec": TIME_PROXIMITY_SEC,
                    "member_count": len(group_incidents),
                },
            )
            db.add(grp)
            db.flush()
            for inc in group_incidents:
                db.add(CorrelatedIncident(correlation_group_id=grp.id, incident_id=inc.id))
            db.commit()
            node_pks = [inc.node_id for inc in group_incidents]
            nodes = db.query(Node).filter(Node.id.in_(node_pks)).all()
            groups_out.append({
                "group_id": grp.id,
                "root_cause_summary": summary,
                "incident_ids": [inc.incident_id for inc in group_incidents],
                "node_ids": [n.node_id for n in nodes],
            })

    return groups_out


def get_correlated_groups(db: Session, limit: int = 50) -> List[dict]:
    """Return stored correlation groups with members."""
    groups = (
        db.query(IncidentCorrelationGroup)
        .order_by(desc(IncidentCorrelationGroup.created_at))
        .limit(limit)
        .all()
    )
    result = []
    for g in groups:
        members = db.query(CorrelatedIncident).filter(CorrelatedIncident.correlation_group_id == g.id).all()
        inc_ids = [m.incident_id for m in members]
        incidents = db.query(Incident).filter(Incident.id.in_(inc_ids)).all()
        node_pks = list({i.node_id for i in incidents})
        nodes = db.query(Node).filter(Node.id.in_(node_pks)).all()
        result.append({
            "group_id": g.id,
            "root_cause_summary": g.root_cause_summary,
            "created_at": g.created_at.isoformat() if g.created_at else None,
            "incident_ids": [i.incident_id for i in incidents],
            "affected_nodes": [n.node_id for n in nodes],
        })
    return result
