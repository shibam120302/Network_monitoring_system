#!/usr/bin/env python3
"""Run a single monitoring agent (collects metrics and POSTs to central API)."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.agents.collector import run_agent_loop
from backend.config import get_settings

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Run monitoring agent for one node")
    p.add_argument("--node-id", default="node-1", help="Node ID (e.g. node-1)")
    p.add_argument("--interval", type=int, default=None, help="Seconds between collections (default from config)")
    p.add_argument("--api", default=None, help="Central API base URL (default from config)")
    p.add_argument("--target-host", default=None, help="Target host for ping/SNMP (default: node-id or 127.0.0.1)")
    args = p.parse_args()
    settings = get_settings()
    interval = args.interval or settings.METRICS_INTERVAL_SEC
    api_base = args.api or settings.CENTRAL_API_URL
    run_agent_loop(args.node_id, interval, api_base, args.target_host)
