# AI-Powered Automated Network Monitoring and Self-Healing System

A production-grade distributed network monitoring platform for 100+ nodes, featuring advanced monitoring capabilities:

- **Predictive Failure Detection**: Uses machine learning to forecast failures before they occur.
- **Root Cause Analysis**: Automated diagnosis of incident origins.
- **Event Correlation**: Links related events for actionable insights.
- **Streaming Pipeline**: Real-time data processing and anomaly detection.
- **Chaos Engineering Simulator**: Test system resilience by injecting faults and observing recovery.

Automatic remediation, alerting, AI-powered incident reports, and an AI chat agent for natural-language queries about network state.

## Architecture

```
Monitoring Agents → FastAPI Monitoring Service → PostgreSQL (metrics + incidents)
                            ↓
                  Event Correlation Engine
                            ↓
                  Predictive Failure Detection (ML)
                            ↓
                  Incident Detection & Root Cause Analysis
                            ↓
                  Streaming Pipeline & Chaos Simulator
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
- **ML:** scikit-learn Isolation Forest, custom predictive models
- **Event Correlation:** Custom engine
- **Root Cause Analysis:** Automated diagnosis module
- **Streaming:** Kafka, custom stream processors
- **Chaos Engineering:** Fault injection simulator
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

## Advanced Features Usage

- **Predictive Failure Detection**: View predictions in dashboard or via API endpoint `/predictions`.
- **Root Cause Analysis**: Access results in dashboard or via `/root_cause` endpoint.
- **Event Correlation**: Correlated events shown in dashboard and `/correlated` endpoint.
- **Streaming Pipeline**: Real-time metrics and anomalies processed via Kafka and shown in dashboard.
- **Chaos Engineering Simulator**: Launch simulations from dashboard or `/chaos` endpoint to test resilience.

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

| Method | Endpoint                            | Description                                                                               |
| ------ | ----------------------------------- | ----------------------------------------------------------------------------------------- |
| POST   | `/api/v1/metrics`                   | Ingest metrics from agents                                                                |
| GET    | `/api/v1/nodes`                     | List nodes with latest metrics                                                            |
| GET    | `/api/v1/nodes/{id}/metrics`        | Metric history for a node                                                                 |
| GET    | `/api/v1/incidents`                 | List incidents (optional filters)                                                         |
| GET    | `/api/v1/incidents/{id}`            | Incident detail + timeline                                                                |
| GET    | `/api/v1/incidents/{id}/root-cause` | **Root cause analysis** for incident                                                      |
| GET    | `/api/v1/incidents/correlated`      | **Correlated incident groups**                                                            |
| GET    | `/api/v1/topology`                  | Network topology (nodes + edges)                                                          |
| GET    | `/api/v1/reports/daily`             | Daily AI report (generate or get)                                                         |
| GET    | `/api/v1/reports/daily/download`    | Download daily report PDF                                                                 |
| GET    | `/api/v1/sla`                       | SLA metrics (uptime %, MTTR, MTBF)                                                        |
| GET    | `/api/v1/predictions`               | **ML failure predictions** (probability + predicted issue)                                |
| POST   | `/api/v1/ai/chat`                   | AI chat (questions about network)                                                         |
| POST   | `/api/v1/simulate/latency`          | Simulate latency spike                                                                    |
| POST   | `/api/v1/simulate/packet_loss`      | Simulate packet loss                                                                      |
| POST   | `/api/v1/simulate/link_failure`     | Simulate link failure                                                                     |
| POST   | `/api/v1/simulate/cpu_spike`        | Simulate CPU spike                                                                        |
| POST   | `/api/v1/chaos/simulate`            | **Chaos engineering** (packet_loss, high_latency, cpu_spike, link_failure, node_shutdown) |
| GET    | `/api/v1/chaos/runs`                | List chaos simulation runs                                                                |

## Features

### Core

- **Distributed monitoring agents:** Ping, SNMP, Netmiko; metrics every 30s to central API (REST or Kafka).
- **Incident detection:** Rule-based (latency > 100ms, packet loss > 5%, CPU > 90%, interface down, node unreachable).
- **Automated remediation:** Restart interface/service/agent via Netmiko (or simulated when no device).
- **Email alerts:** SMTP on incident detection (configure SMTP\_\* in `.env`).
- **Failure simulation:** Inject latency, packet loss, link failure, CPU spike for testing.
- **Topology:** NetworkX-based graph; API returns nodes and edges with status.
- **Daily AI report:** Aggregates incidents, downtime, remediation rate, health score; AI summary + PDF download.
- **AI chat agent:** Natural-language answers using DB context and OpenAI/local LLM.
- **Incident timeline:** Per-incident events (detected, created, remediation_triggered, resolved).
- **SLA metrics:** Uptime %, MTTR, MTBF over configurable period.
- **Optional ML:** Isolation Forest for anomaly detection on metrics.

### Advanced (production-level)

- **Predictive failure detection (AI):** ML model (Isolation Forest / Random Forest) on latency, packet_loss, cpu, memory, bandwidth; predicts probability of node failure in 10–30 minutes and predicted cause. `GET /predictions`.
- **Intelligent root cause analysis:** Uses topology graph, metric correlations, and neighboring node failures to infer root cause (e.g. congestion at upstream node). `GET /incidents/{id}/root-cause`.
- **Event correlation engine:** Groups related alerts by time proximity, topology, and metric similarity into single incidents to reduce noise. Stored in DB. `GET /incidents/correlated`.
- **Real-time metrics streaming (Kafka):** Optional pipeline: agents → Kafka topic → stream consumer → anomaly detection → PostgreSQL. Set `KAFKA_BOOTSTRAP_SERVERS` and optionally run Kafka consumer (Celery task or standalone).
- **Chaos engineering simulator:** Inject failures (node_shutdown, packet_loss, high_latency, network_partition, cpu_spike), verify detection and remediation, log results. `POST /chaos/simulate`, `GET /chaos/runs`.
- **Daily report extended:** AI report now includes predicted failures count, correlated incident groups, root cause summaries, and chaos simulation results (detection/remediation rate).
- **OpenTelemetry:** Optional tracing when `OTEL_EXPORTER_OTLP_ENDPOINT` is set.

## Project Structure

```
network-monitoring-system/
├── backend/
│   ├── agents/            # Monitoring agent (collector) + optional Kafka producer
│   ├── incident_engine/   # Rule-based detection
│   ├── remediation_engine/
│   ├── alerts/            # SMTP
│   ├── ai_agent/          # Chat
│   ├── reporting_service/ # Daily AI report (includes predictions, correlated, chaos)
│   ├── simulation/        # Failure simulation
│   ├── topology/          # NetworkX topology
│   ├── ml_anomaly/        # Isolation Forest (legacy)
│   ├── ml_prediction/     # Predictive failure detection (Isolation Forest / Random Forest)
│   ├── root_cause_engine/ # Intelligent root cause analysis
│   ├── event_correlation/ # Alert correlation (time, topology, metric similarity)
│   ├── stream_processing/ # Kafka consumer + producer
│   ├── chaos_engine/      # Chaos engineering simulator
│   ├── routers/           # FastAPI routes
│   ├── tasks/             # Celery tasks (monitoring, reports, stream_consumer)
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
