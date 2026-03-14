# How to Run the Project – Full Guide

This document explains how to run the **AI-Powered Network Monitoring and Self-Healing System** in full detail: UI only, with Docker (all services), or locally (without Docker).

---

## Table of contents

1. [UI only (dashboard without backend)](#1-ui-only-dashboard-without-backend)
2. [Run with Docker (full stack)](#2-run-with-docker-full-stack)
3. [Run locally without Docker](#3-run-locally-without-docker)
4. [Optional: Run monitoring agents](#4-optional-run-monitoring-agents)
5. [Optional: Celery workers (local)](#5-optional-celery-workers-local)
6. [Verify everything is working](#6-verify-everything-is-working)
7. [Troubleshooting](#7-troubleshooting)

---

## 1. UI only (dashboard without backend)

Use this to **see only the React dashboard** (layout, navigation, no real data).

### Prerequisites

- **Node.js** 16 or newer
  - Check: `node --version`
  - Install: https://nodejs.org/

### Steps

1. Open **PowerShell** or **Command Prompt**.

2. Go to the dashboard folder (use your actual project path if different):

   ```powershell
   cd c:\Users\shiba\Downloads\ANMIR\network-monitoring-system\dashboard
   ```

3. Install dependencies (first time only; may take 1–2 minutes):

   ```powershell
   npm install
   ```

4. Start the development server:

   ```powershell
   npm start
   ```

5. Your browser should open automatically to **http://localhost:3000**.  
   If not, open that URL manually.

### What you see

- **Navigation:** Dashboard, Nodes, Incidents, Topology, Reports, SLA, AI Chat, Simulate.
- **Dashboard:** Stat cards, chart placeholders, incidents table.
- **Without backend:** Tables and lists will be empty or show “Loading…” / “No nodes” because the API is not running. The **UI and all pages still load**.

---

## 2. Run with Docker (full stack)

Runs **PostgreSQL**, **Redis**, **API**, **Celery worker**, **Celery beat**, and **Dashboard** in containers. No need to install Python, Node, PostgreSQL, or Redis on your machine.

### Prerequisites

- **Docker Desktop** (includes Docker and Docker Compose)
  - Windows: https://docs.docker.com/desktop/install/windows-install/
  - After install, start Docker Desktop and wait until it is running (whale icon in system tray).

### Step 1: Open terminal in project root

```powershell
cd c:\Users\shiba\Downloads\ANMIR\network-monitoring-system
```

Make sure you are in the folder that contains `backend`, `dashboard`, `docker`, and `requirements.txt`.

### Step 2: Create environment file

Create a `.env` file so the API can load config (optional; Docker Compose overrides key vars inside the network):

```powershell
copy .env.example .env
```

You can edit `.env` later to set SMTP, OpenAI key, etc. For a first run, the defaults are fine.

### Step 3: Start all services

```powershell
cd docker
docker-compose up -d
```

- `-d` runs containers in the background.
- First time: Docker will **build** the API and dashboard images (can take several minutes).
- Wait **about 30–60 seconds** for PostgreSQL and Redis to become healthy and for the API to start.

### Step 4: Check that containers are running

```powershell
docker-compose ps
```

You should see something like:

- `nm-postgres` (port 5432) – running
- `nm-redis` (port 6379) – running
- `nm-api` (port 8000) – running
- `nm-celery-worker` – running
- `nm-celery-beat` – running
- `nm-dashboard` (port 3000) – running

If the API container keeps restarting, check logs:

```powershell
docker-compose logs api
```

### Step 5: Seed sample data (102 nodes + sample metrics)

From the **project root** (not inside `docker`), run the seed script **inside** the API container:

```powershell
cd c:\Users\shiba\Downloads\ANMIR\network-monitoring-system
docker exec nm-api python scripts/seed_nodes.py
```

You should see: `Seeded 102 nodes, topology links, and sample metrics.`

### Step 6: Open the application

- **Dashboard (UI):** http://localhost:3000
- **API docs (Swagger):** http://localhost:8000/docs
- **API health:** http://localhost:8000/health
- **Nodes (JSON):** http://localhost:8000/api/v1/nodes

### Stopping Docker

From the `docker` folder:

```powershell
cd c:\Users\shiba\Downloads\ANMIR\network-monitoring-system\docker
docker-compose down
```

Data in PostgreSQL is kept in a Docker volume. To remove volumes too (wipe DB):

```powershell
docker-compose down -v
```

---

## 3. Run locally without Docker

Run the **API**, **dashboard**, and optionally **Celery** on your machine. You must install **Python**, **PostgreSQL**, and **Redis** yourself.

### Prerequisites

- **Python 3.11 or 3.12**
  - Check: `python --version` or `py --version`
  - Install: https://www.python.org/downloads/

- **PostgreSQL 14+**
  - Install: https://www.postgresql.org/download/windows/
  - During setup, note the password you set for the `postgres` user.
  - Ensure PostgreSQL is **running** (e.g. Windows Service “postgresql-x64-15”).

- **Redis**
  - Windows: https://github.com/microsoftarchive/redis/releases (e.g. Redis-x64-3.0.504.msi)
  - Or use WSL and install Redis there, then use `localhost` from Windows.
  - Ensure Redis is **running** (default port 6379).

- **Node.js 16+** (for the dashboard)
  - Install: https://nodejs.org/

### Step 1: Create database and user in PostgreSQL

Using **pgAdmin**, **psql**, or any PostgreSQL client, run:

```sql
CREATE USER monitor WITH PASSWORD 'monitor';
CREATE DATABASE network_monitoring OWNER monitor;
```

If you use a different user/password, you will set them in `.env` in the next step.

### Step 2: Open terminal in project root

```powershell
cd c:\Users\shiba\Downloads\ANMIR\network-monitoring-system
```

### Step 3: Create virtual environment and install Python dependencies

```powershell
python -m venv venv
.\venv\Scripts\activate
```

Your prompt should show `(venv)`. Then:

```powershell
pip install -r requirements.txt
```

Installation may take a few minutes.

### Step 4: Create and edit `.env`

```powershell
copy .env.example .env
notepad .env
```

Set at least these (adjust if your PostgreSQL/Redis are different):

```env
DATABASE_URL=postgresql://monitor:monitor@localhost:5432/network_monitoring
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
CENTRAL_API_URL=http://localhost:8000
```

Save and close.

### Step 5: Run the API (Terminal 1)

Keep this terminal open:

```powershell
cd c:\Users\shiba\Downloads\ANMIR\network-monitoring-system
.\venv\Scripts\activate
$env:PYTHONPATH = (Get-Location).Path
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

You should see:

- `Uvicorn running on http://0.0.0.0:8000`
- On first request, the app creates DB tables (no separate migration needed for this setup).

### Step 6: Seed sample data (Terminal 2)

Open a **new** PowerShell window:

```powershell
cd c:\Users\shiba\Downloads\ANMIR\network-monitoring-system
.\venv\Scripts\activate
$env:PYTHONPATH = (Get-Location).Path
python scripts/seed_nodes.py
```

Expected output: `Seeded 102 nodes, topology links, and sample metrics.`

### Step 7: Run the dashboard (Terminal 3)

Open another PowerShell window:

```powershell
cd c:\Users\shiba\Downloads\ANMIR\network-monitoring-system\dashboard
npm install
$env:REACT_APP_API_URL = "http://localhost:8000"
npm start
```

The browser should open to **http://localhost:3000**. The dashboard will call the API at `http://localhost:8000` for data.

### Summary of local run

| Terminal | Command / role                                                       |
| -------- | -------------------------------------------------------------------- |
| 1        | `uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000` – API |
| 2        | `python scripts/seed_nodes.py` – seed once                           |
| 3        | `npm start` in `dashboard/` – UI                                     |

---

## 4. Optional: Run monitoring agents

Agents collect metrics (ping, SNMP, etc.) and POST them to the central API. You can run one or more agents.

### With Docker (API already running)

```powershell
docker exec -it nm-api python scripts/run_agent.py --node-id node-1 --interval 30
```

This runs the agent **inside** the API container; it will POST to the same API. Press Ctrl+C to stop.

### Locally (API running on localhost:8000)

```powershell
cd c:\Users\shiba\Downloads\ANMIR\network-monitoring-system
.\venv\Scripts\activate
$env:PYTHONPATH = (Get-Location).Path
python scripts/run_agent.py --node-id node-1 --api http://localhost:8000 --interval 30
```

Options:

- `--node-id` – e.g. `node-1`, `node-2` (must exist or will be created when first metrics arrive).
- `--api` – base URL of the API (default from `.env`).
- `--interval` – seconds between collections (default 30).
- `--target-host` – host to ping/SNMP (default derived from node-id or 127.0.0.1).

---

## 5. Optional: Celery workers (local)

If you run **without Docker**, you can still run Celery for periodic tasks (e.g. daily report) and for task queues.

**Terminal 4 – Celery worker:**

```powershell
cd c:\Users\shiba\Downloads\ANMIR\network-monitoring-system
.\venv\Scripts\activate
$env:PYTHONPATH = (Get-Location).Path
celery -A backend.celery_app worker -l info -Q monitoring,remediation,reports
```

**Terminal 5 – Celery beat (scheduler):**

```powershell
cd c:\Users\shiba\Downloads\ANMIR\network-monitoring-system
.\venv\Scripts\activate
$env:PYTHONPATH = (Get-Location).Path
celery -A backend.celery_app beat -l info
```

With Docker, the Compose file already starts worker and beat; you don’t need to run these manually.

---

## 6. Verify everything is working

Use this checklist after starting the stack (Docker or local).

| Step | Action                                                                  | Expected result                                                |
| ---- | ----------------------------------------------------------------------- | -------------------------------------------------------------- |
| 1    | Open **http://localhost:8000/health** in browser                        | JSON: `{"status":"ok","service":"Network Monitoring System"}`  |
| 2    | Open **http://localhost:8000/api/v1/nodes**                             | JSON array of nodes (e.g. 102 after seed)                      |
| 3    | Open **http://localhost:8000/docs**                                     | Swagger UI with all API endpoints                              |
| 4    | Open **http://localhost:3000**                                          | Dashboard with “Total Nodes”, “Up”, “Active Incidents”, charts |
| 5    | In dashboard: **Nodes**                                                 | Table with node IDs, status, latency, CPU, etc.                |
| 6    | In dashboard: **Simulate** → node `node-1` → **Simulate latency spike** | Message like “Latency spike simulated”                         |
| 7    | In dashboard: **Incidents**                                             | List of incidents (may include one from step 6)                |
| 8    | In dashboard: **Topology**                                              | Graph of nodes and links (if topology was seeded)              |
| 9    | In dashboard: **Reports** → Regenerate / Download PDF                   | Report with summary and optional PDF                           |
| 10   | In dashboard: **AI Chat** → e.g. “Which nodes are failing?”             | A text reply (uses OpenAI if key set, else fallback)           |

If steps 1–4 work, the core stack is running. Steps 5–10 confirm data, simulation, and features.

---

## 7. Troubleshooting

### API won’t start (Docker)

- **Check logs:** `docker-compose logs api`
- **Database not ready:** Wait longer after `docker-compose up -d`, or run seed again after 1–2 minutes.
- **Port 8000 in use:** Stop the other app using 8000, or change the API port in `docker-compose.yml` (e.g. `"8001:8000"`) and use `http://localhost:8001` for API and dashboard `REACT_APP_API_URL`.

### API won’t start (local)

- **“ModuleNotFoundError”:** Ensure venv is activated and you ran `pip install -r requirements.txt`. Set `PYTHONPATH` to project root: `$env:PYTHONPATH = (Get-Location).Path`.
- **Database connection error:** Check PostgreSQL is running, and that `DATABASE_URL` in `.env` matches your DB (user `monitor`, database `network_monitoring`, port 5432).
- **Redis connection error:** Check Redis is running on port 6379; set `REDIS_URL` in `.env`.

### Dashboard shows “Loading…” or empty lists

- API must be running and reachable. Open http://localhost:8000/health; if it fails, fix the API first.
- If running dashboard with `npm start`, set `REACT_APP_API_URL=http://localhost:8000` so the UI calls the right host (or rely on `proxy` in `dashboard/package.json` when API is on same host).
- Run the seed script so nodes and metrics exist: `python scripts/seed_nodes.py` (local) or `docker exec nm-api python scripts/seed_nodes.py` (Docker).

### Seed script fails

- **“connection refused” / “could not connect”:** Start the API first, then run the seed script. For Docker, ensure the API container is healthy before running `docker exec nm-api python scripts/seed_nodes.py`.
- **“role monitor does not exist”:** Create the PostgreSQL user and database as in [Step 1 of “Run locally”](#step-1-create-database-and-user-in-postgresql).

### Docker build fails

- Ensure Docker Desktop is running and you have enough disk space.
- From project root run: `cd docker` then `docker-compose build --no-cache` to see full build output.

### Port already in use

- **5432:** Another PostgreSQL instance. Stop it or change the host port in `docker-compose.yml` (e.g. `"5433:5432"`).
- **6379:** Another Redis. Stop it or change the port mapping.
- **8000:** Another app. Use a different host port for the API (e.g. `"8001:8000"`) and set `REACT_APP_API_URL=http://localhost:8001` for the dashboard.
- **3000:** Another React or Node app. Use another port: in `dashboard/package.json` you can set `"start": "PORT=3001 react-scripts start"` (or on Windows use `set PORT=3001 && npm start`).

---

## Quick reference – URLs

| What               | URL                                        |
| ------------------ | ------------------------------------------ |
| Dashboard (UI)     | http://localhost:3000                      |
| API health         | http://localhost:8000/health               |
| API docs (Swagger) | http://localhost:8000/docs                 |
| Nodes API          | http://localhost:8000/api/v1/nodes         |
| Incidents API      | http://localhost:8000/api/v1/incidents     |
| Topology API       | http://localhost:8000/api/v1/topology      |
| Daily report       | http://localhost:8000/api/v1/reports/daily |
