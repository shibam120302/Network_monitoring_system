"""Build network topology graph with NetworkX."""
from typing import List, Dict, Any
from sqlalchemy.orm import Session
import networkx as nx

from database.models import Node, TopologyLink, Metric
from sqlalchemy import desc


def build_topology(db: Session) -> Dict[str, Any]:
    """Build topology: nodes (with status from latest metrics) and edges from topology_links."""
    nodes = db.query(Node).filter(Node.is_active == True).all()
    links = db.query(TopologyLink).all()

    G = nx.Graph()
    node_status = {}

    for node in nodes:
        nid = node.node_id
        G.add_node(nid, label=node.hostname or nid, ip=node.ip_address)
        # Status from latest metric
        latest = (
            db.query(Metric)
            .filter(Metric.node_id == node.id)
            .order_by(desc(Metric.timestamp))
            .first()
        )
        if not latest:
            node_status[nid] = "unknown"
        elif latest.interface_status and str(latest.interface_status).lower() == "down":
            node_status[nid] = "down"
        elif latest.latency_ms and latest.latency_ms > 200:
            node_status[nid] = "degraded"
        else:
            node_status[nid] = "up"

    for link in links:
        src = db.query(Node).filter(Node.id == link.source_node_id).first()
        tgt = db.query(Node).filter(Node.id == link.target_node_id).first()
        if src and tgt:
            G.add_edge(
                src.node_id,
                tgt.node_id,
                bandwidth_mbps=link.bandwidth_mbps,
                is_up=link.is_up,
            )

    # Serialize for API
    nodes_out = [
        {"id": n, "label": G.nodes[n].get("label", n), "status": node_status.get(n, "unknown"), "ip": G.nodes[n].get("ip")}
        for n in G.nodes()
    ]
    edges_out = [
        {
            "source": u,
            "target": v,
            "bandwidth_mbps": G.edges[u, v].get("bandwidth_mbps"),
            "is_up": G.edges[u, v].get("is_up", True),
        }
        for u, v in G.edges()
    ]

    return {
        "nodes": nodes_out,
        "edges": edges_out,
        "graph_json": {
            "nodes": list(G.nodes()),
            "edges": list(G.edges()),
        },
    }
