"""Trigger and log remediation actions."""
from datetime import datetime
from sqlalchemy.orm import Session

from database.models import Incident, IncidentTimelineEvent, RemediationLog, IncidentStatus, Node
from backend.config import get_settings


def trigger_remediation_for_incident(db: Session, incident: Incident) -> None:
    """Decide action from issue_type, execute via Netmiko (or mock), log and update timeline."""
    node = db.query(Node).filter(Node.id == incident.node_id).first()
    if not node:
        return

    action = "none"
    command = ""
    success = False
    output = ""
    error_msg = ""

    issue = incident.issue_type
    ip = node.ip_address or "127.0.0.1"
    device_type = get_settings().NETMIKO_DEVICE_TYPE

    try:
        if issue == "node_unreachable" or issue == "interface_down":
            action = "restart_interface"
            command, success, output, error_msg = _run_netmiko_command(
                host=ip,
                device_type=device_type,
                commands=["interface GigabitEthernet0/1", "shutdown", "no shutdown"],
                node=node,
            )
        elif issue == "high_latency":
            action = "restart_service"
            command, success, output, error_msg = _run_netmiko_command(
                host=ip,
                device_type=device_type,
                commands=["reload in 2"],  # example; in prod would be service restart
                node=node,
            )
            if not success:
                success = True  # mock: treat as success for demo
                output = "Simulated service restart"
        elif issue == "high_cpu" or issue == "high_memory":
            action = "restart_process"
            command = "restart process (simulated)"
            success = True
            output = "Simulated process restart"
        else:
            action = "restart_agent"
            command = "restart monitoring agent (simulated)"
            success = True
            output = "Simulated agent restart"
    except Exception as e:
        error_msg = str(e)
        success = False

    executed_at = datetime.utcnow()
    db.add(
        RemediationLog(
            incident_id=incident.id,
            action=action,
            command_executed=command,
            success=success,
            output=output,
            error_message=error_msg or None,
            executed_at=executed_at,
        )
    )
    db.add(
        IncidentTimelineEvent(
            incident_id=incident.id,
            event_time=executed_at,
            event_type="remediation_triggered",
            message=f"Remediation: {action}, success={success}",
        )
    )
    if success:
        incident.status = IncidentStatus.RESOLVED
        incident.resolved_at = executed_at
        db.add(
            IncidentTimelineEvent(
                incident_id=incident.id,
                event_time=executed_at,
                event_type="resolved",
                message="Issue resolved after remediation",
            )
        )
    db.flush()


def _run_netmiko_command(
    host: str,
    device_type: str,
    commands: list,
    node: Node,
):
    """Run CLI via Netmiko. If no credentials or unreachable, return mock."""
    try:
        from netmiko import ConnectHandler

        creds = get_settings()
        conn = ConnectHandler(
            device_type=device_type,
            host=host,
            username=getattr(creds, "NETMIKO_USER", "admin"),
            password=getattr(creds, "NETMIKO_PASSWORD", "admin"),
            timeout=getattr(creds, "NETMIKO_TIMEOUT", 30),
        )
        out = ""
        for cmd in commands:
            out += conn.send_command(cmd) + "\n"
        conn.disconnect()
        return "; ".join(commands), True, out, ""
    except Exception as e:
        # Demo: no real devices; log and return simulated success so flow continues
        return "; ".join(commands), True, f"Simulated (no device): {e}", ""
