# AI-Powered Automated Network Monitoring and Self-Healing System

A production-grade distributed network monitoring platform that detects failures across 100+ nodes, automatically remediates issues, sends alerts, and generates AI-powered incident reports. Includes an AI chat agent for natural-language queries about network state.

## Architecture

```
Monitoring Agents → FastAPI Monitoring Service → PostgreSQL (metrics + incidents)
                            ↓
                  Incident Detection Engine
                            ↓
                  Automated Remediation Engine
                            ↓
                  Alert Service (Email) + AI Report Generator + AI Chat Agent
                            ↓
                  Dashboard (React)
```

## Tech Stack

- **Backend:** Python, FastAPI
- **Database:** PostgreSQL (metrics, incidents, topology, reports, SLA)
- **Cache/Queue:** Redis, Celery
- **Network:** SNMP, Ping (ping3), Netmiko
- **AI:** OpenAI API or local LLM (Ollama) for reports and chat
- **ML:** scikit-learn Isolation Forest (optional anomaly detection)
- **Topology:** NetworkX
- **Reports:** ReportLab (PDF)
- **Frontend:** React, Chart.js
- **Containers:** Docker, docker-compose

## Quick Start

### With Docker

1. Clone and enter the project:
   ```bash
   cd network-monitoring-system
   ```

2. Copy environment file and optionally edit:
   ```bash
   cp .env.example .env
   ```

3. Start stack (PostgreSQL, Redis, API, Celery worker, Celery beat, Dashboard):
   ```bash
   cd docker
   docker-compose up -d
   ```

4. Seed 102 nodes and sample metrics (run from project root, with API reachable):
   ```bash
   # From host (ensure API is up)
   python scripts/seed_nodes.py
   ```
   Or run inside API container:
   ```bash
   docker exec -it nm-api python scripts/seed_nodes.py
   ```

5. Open:
   - **Dashboard:** http://localhost:3000
   - **API docs:** http://localhost:8000/docs
   - **API health:** http://localhost:8000/health

### Without Docker (local dev)

1. Install PostgreSQL and Redis, create DB:
   ```bash
   createdb network_monitoring
   # create user monitor / password monitor if needed
   ```

2. Create venv and install deps:
   ```bash
   python -m venv venv
   source venv/bin/activate   # or venv\Scripts\activate on Windows
   pip install -r requirements.txt
   ```

3. Set `.env` (copy from `.env.example`), then:
   ```bash
   export PYTHONPATH=$PWD
   uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
   ```

4. Seed data:
   ```bash
   python scripts/seed_nodes.py
   ```

5. Run dashboard (separate terminal):
   ```bash
   cd dashboard && npm install && npm start
   ```
   Set `REACT_APP_API_URL=http://localhost:8000` if not using proxy.

6. Optional: run Celery worker and beat for periodic tasks and report generation:
   ```bash
   celery -A backend.celery_app worker -l info -Q monitoring,remediation,reports
   celery -A backend.celery_app beat -l info
   ```

## Running Monitoring Agents

Agents collect metrics every 30s (configurable) and POST to the central API.

**Single agent (standalone):**
```bash
python -m backend.agents.collector --node-id node-1 --interval 30 --api http://localhost:8000
```

Or from project root:
```bash
python backend/agents/collector.py --node-id node-1
```

For 100+ nodes, run one process per node or use Celery to dispatch `collect_and_send_metrics` tasks per node.

## API Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/metrics` | Ingest metrics from agents |
| GET | `/api/v1/nodes` | List nodes with latest metrics |
| GET | `/api/v1/nodes/{id}/metrics` | Metric history for a node |
| GET | `/api/v1/incidents` | List incidents (optional filters) |
| GET | `/api/v1/incidents/{id}` | Incident detail + timeline |
| GET | `/api/v1/topology` | Network topology (nodes + edges) |
| GET | `/api/v1/reports/daily` | Daily AI report (generate or get) |
| GET | `/api/v1/reports/daily/download` | Download daily report PDF |
| GET | `/api/v1/sla` | SLA metrics (uptime %, MTTR, MTBF) |
| POST | `/api/v1/ai/chat` | AI chat (questions about network) |
| POST | `/api/v1/simulate/latency` | Simulate latency spike |
| POST | `/api/v1/simulate/packet_loss` | Simulate packet loss |
| POST | `/api/v1/simulate/link_failure` | Simulate link failure |
| POST | `/api/v1/simulate/cpu_spike` | Simulate CPU spike |

## Features

- **Distributed monitoring agents:** Ping, SNMP, Netmiko; metrics every 30s to central API.
- **Incident detection:** Rule-based (latency > 100ms, packet loss > 5%, CPU > 90%, interface down, node unreachable).
- **Automated remediation:** Restart interface/service/agent via Netmiko (or simulated when no device).
- **Email alerts:** SMTP on incident detection (configure SMTP_* in `.env`).
- **Failure simulation:** Inject latency, packet loss, link failure, CPU spike for testing.
- **Topology:** NetworkX-based graph; API returns nodes and edges with status.
- **Daily AI report:** Aggregates incidents, downtime, remediation rate, health score; AI summary + PDF download.
- **AI chat agent:** Natural-language answers using DB context and OpenAI/local LLM.
- **Incident timeline:** Per-incident events (detected, created, remediation_triggered, resolved).
- **SLA metrics:** Uptime %, MTTR, MTBF over configurable period.
- **Optional ML:** Isolation Forest for anomaly detection on metrics.

## Project Structure

```
network-monitoring-system/
├── backend/
│   ├── agents/          # Monitoring agent (collector)
│   ├── monitoring_service/  # (integrated in main)
│   ├── incident_engine/ # Rule-based + ML detection
│   ├── remediation_engine/
│   ├── alerts/          # SMTP
│   ├── ai_agent/        # Chat
│   ├── reporting_service/
│   ├── simulation/
│   ├── topology/
│   ├── ml_anomaly/      # Isolation Forest
│   ├── routers/         # FastAPI routes
│   ├── tasks/           # Celery tasks
│   ├── config.py
│   ├── main.py
│   └── celery_app.py
├── database/
│   ├── models.py
│   └── session.py
├── dashboard/           # React app
├── docker/
│   ├── docker-compose.yml
│   ├── Dockerfile.api
│   ├── Dockerfile.dashboard
│   └── nginx.conf
├── scripts/
│   └── seed_nodes.py
├── requirements.txt
├── .env.example
└── README.md
```

## Configuration

See `.env.example`. Important variables:

- `DATABASE_URL` – PostgreSQL connection string.
- `REDIS_URL`, `CELERY_BROKER_URL` – Redis.
- `SMTP_*`, `ALERT_EMAIL_TO` – Email alerts.
- `OPENAI_API_KEY`, `OPENAI_MODEL` – AI report and chat (or `USE_LOCAL_LLM=true` and `LOCAL_LLM_BASE_URL` for Ollama).
- `THRESHOLD_LATENCY_MS`, `THRESHOLD_PACKET_LOSS_PCT`, `THRESHOLD_CPU_PCT` – Detection thresholds.
- `CENTRAL_API_URL` – Used by agents and simulation to POST metrics (e.g. `http://api:8000` in Docker).

## License

MIT.
