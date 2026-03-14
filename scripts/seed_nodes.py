"""Seed 100+ nodes and optional topology links + sample metrics."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
import random
from database.session import get_sync_session, get_engine
from database.models import Base, Node, Metric, TopologyLink
from backend.config import get_settings


def seed():
    settings = get_settings()
    engine = get_engine(settings.DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    db = get_sync_session()
    try:
        # Create 102 nodes
        nodes = []
        for i in range(1, 103):
            node_id = f"node-{i}"
            if db.query(Node).filter(Node.node_id == node_id).first():
                continue
            n = Node(
                node_id=node_id,
                hostname=f"host-{i}",
                ip_address=f"10.0.{i // 256}.{i % 256}" if i < 256 else "10.1.0.1",
                device_type="cisco_ios",
                snmp_community="public",
            )
            db.add(n)
            nodes.append(n)
        db.commit()
        for n in nodes:
            db.refresh(n)

        # Topology: linear + some branches (node1-node2-node3, node1-node4, etc.)
        all_nodes = db.query(Node).order_by(Node.id).all()
        for i, n in enumerate(all_nodes[:20]):
            if i + 1 < len(all_nodes):
                t = all_nodes[i + 1]
                if not db.query(TopologyLink).filter(
                    TopologyLink.source_node_id == n.id,
                    TopologyLink.target_node_id == t.id,
                ).first():
                    db.add(TopologyLink(source_node_id=n.id, target_node_id=t.id, link_name=f"link-{n.node_id}-{t.node_id}", bandwidth_mbps=1000, is_up=True))
        db.commit()

        # Sample metrics for last 24h for first 20 nodes
        for node in all_nodes[:20]:
            base_ts = datetime.utcnow() - timedelta(hours=24)
            for h in range(24):
                for _ in range(2):
                    ts = base_ts + timedelta(hours=h, minutes=random.randint(0, 59))
                    db.add(Metric(
                        node_id=node.id,
                        latency_ms=random.uniform(5, 80),
                        packet_loss_pct=random.uniform(0, 2),
                        cpu_usage_pct=random.uniform(20, 70),
                        memory_usage_pct=random.uniform(40, 60),
                        interface_status="up",
                        bandwidth_usage_mbps=random.uniform(100, 800),
                        timestamp=ts,
                    ))
        db.commit()
        print("Seeded 102 nodes, topology links, and sample metrics.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
