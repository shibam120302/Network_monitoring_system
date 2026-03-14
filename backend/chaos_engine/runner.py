"""
Chaos engineering simulator: inject failures (node shutdown, packet loss, latency, partition, CPU spike),
trigger detection and remediation, verify and log results.
"""
import logging
import time
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

from database.models import Node, Incident, ChaosSimulationRun
from backend.config import get_settings
import httpx

logger = logging.getLogger(__name__)

FAILURE_TYPES = ["packet_loss", "high_latency", "cpu_spike", "link_failure", "node_shutdown"]
# node_shutdown = simulate unreachable (no metrics); link_failure = interface down


def run_chaos_simulation(
    db: Session,
    node_id: str,
    failure_type: str,
    duration_seconds: int = 120,
) -> ChaosSimulationRun:
    """
    Trigger simulated failure, wait for detection (and optionally remediation), record results.
    """
    node = db.query(Node).filter(Node.node_id == node_id).first()
    if not node:
        node = Node(node_id=node_id, hostname=node_id)
        db.add(node)
        db.commit()
        db.refresh(node)

    run = ChaosSimulationRun(
        node_id=node.id,
        failure_type=failure_type,
        started_at=datetime.utcnow(),
        result_log={},
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    base = get_settings().CENTRAL_API_URL
    payload_base = {"node_id": node_id, "timestamp": datetime.utcnow().isoformat()}

    # 1) Trigger failure via simulation API
    if failure_type == "packet_loss":
        payload = {**payload_base, "packet_loss": 25}
    elif failure_type == "high_latency":
        payload = {**payload_base, "latency": 350}
    elif failure_type == "cpu_spike":
        payload = {**payload_base, "cpu_usage": 98}
    elif failure_type == "link_failure":
        payload = {**payload_base, "interface_status": "down"}
    elif failure_type == "node_shutdown":
        payload = {**payload_base, "latency": None, "packet_loss": 100, "cpu_usage": None}
    else:
        payload = {**payload_base, "latency": 200}

    try:
        r = httpx.post(f"{base.rstrip('/')}/api/v1/metrics", json=payload, timeout=10)
        run.result_log["injection_response_status"] = r.status_code
    except Exception as e:
        run.result_log["injection_error"] = str(e)
        db.commit()
        return run

    # 2) Wait and check for incident
    time.sleep(5)
    incidents_after = (
        db.query(Incident)
        .filter(Incident.node_id == node.id, Incident.timestamp >= run.started_at)
        .all()
    )
    run.detection_verified = len(incidents_after) > 0
    if incidents_after:
        inc = incidents_after[0]
        run.incident_id = inc.id
        from database.models import RemediationLog
        remed_count = db.query(RemediationLog).filter(RemediationLog.incident_id == inc.id).count()
        run.remediation_verified = remed_count > 0 or (inc.status in ("resolved", "closed"))

    run.ended_at = datetime.utcnow()
    run.result_log["incidents_created"] = len(incidents_after)
    run.result_log["incident_ids"] = [i.incident_id for i in incidents_after]
    db.commit()
    db.refresh(run)
    return run
