"""Lightweight agent: collect metrics via ping, SNMP, Netmiko and send to central API."""
import time
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from datetime import datetime
from typing import Optional
import httpx

# Optional: ping
def _ping_latency_loss(host: str) -> tuple[Optional[float], Optional[float]]:
    """Return (latency_ms, packet_loss_pct)."""
    try:
        import ping3
        r = ping3.ping(host, timeout=2, unit="ms")
        if r is not None and r is not False:
            return (float(r), 0.0)
        return (None, 100.0)
    except Exception:
        return (None, 100.0)


def _snmp_cpu_memory(host: str, community: str = "public") -> tuple[Optional[float], Optional[float]]:
    """Return (cpu_usage_pct, memory_usage_pct) via SNMP if available."""
    try:
        from pysnmp.hlapi import getCmd, SnmpEngine, CommunityData, UdpTransportTarget, ContextData, ObjectType, ObjectIdentity
        cpu_oid = "1.3.6.1.4.1.9.9.109.1.1.1.1.6.1"  # cisco CPU 1 min
        errInd, errStatus, errIdx, varBinds = next(
            getCmd(
                SnmpEngine(),
                CommunityData(community),
                UdpTransportTarget((host, 161), timeout=2),
                ContextData(),
                ObjectType(ObjectIdentity(cpu_oid)),
            )
        )
        if not errInd and not errStatus and varBinds:
            cpu = float(varBinds[0][1])
            return (min(100, cpu), None)
    except Exception:
        pass
    return (None, None)


def _netmiko_interface_bandwidth(host: str, device_type: str = "cisco_ios") -> tuple[Optional[str], Optional[float]]:
    """Return (interface_status, bandwidth_usage_mbps). Mock if no device."""
    try:
        from netmiko import ConnectHandler
        conn = ConnectHandler(
            device_type=device_type,
            host=host,
            username=os.environ.get("NETMIKO_USER", "admin"),
            password=os.environ.get("NETMIKO_PASSWORD", "admin"),
            timeout=10,
        )
        out = conn.send_command("show interfaces summary")
        conn.disconnect()
        if "down" in out.lower():
            return ("down", None)
        return ("up", None)
    except Exception:
        return ("up", None)  # assume up if unreachable for demo


def collect_metrics(
    node_id: str,
    target_host: Optional[str] = None,
    snmp_community: str = "public",
    device_type: str = "cisco_ios",
) -> dict:
    """Collect all metrics for this node. target_host defaults to node_id or 127.0.0.1."""
    host = target_host or node_id if node_id != "localhost" else "127.0.0.1"
    if host in ("localhost", "127.0.0.1"):
        host = "127.0.0.1"

    latency, packet_loss = _ping_latency_loss(host)
    cpu, memory = _snmp_cpu_memory(host, snmp_community)
    interface_status, bandwidth = _netmiko_interface_bandwidth(host, device_type)

    return {
        "node_id": node_id,
        "latency": latency,
        "packet_loss": packet_loss,
        "cpu_usage": cpu,
        "memory_usage": memory,
        "interface_status": interface_status,
        "bandwidth_usage": bandwidth,
        "timestamp": datetime.utcnow().isoformat(),
    }


def send_metrics(api_base: str, payload: dict) -> bool:
    """POST payload to central API /api/v1/metrics."""
    url = f"{api_base.rstrip('/')}/api/v1/metrics"
    try:
        r = httpx.post(url, json=payload, timeout=10)
        return r.status_code == 200
    except Exception:
        return False


def run_agent_loop(
    node_id: str,
    interval_sec: int = 30,
    api_base: str = "http://localhost:8000",
    target_host: Optional[str] = None,
):
    """Run agent loop: collect every interval_sec and POST to central API."""
    while True:
        payload = collect_metrics(node_id, target_host=target_host)
        ok = send_metrics(api_base, payload)
        print(f"[{datetime.utcnow().isoformat()}] Sent metrics for {node_id}: ok={ok}")
        time.sleep(interval_sec)


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--node-id", default="node-1")
    p.add_argument("--interval", type=int, default=30)
    p.add_argument("--api", default="http://localhost:8000")
    p.add_argument("--target-host", default=None)
    args = p.parse_args()
    run_agent_loop(args.node_id, args.interval, args.api, args.target_host)
