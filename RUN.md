# How to Run and Verify the Project

## Option A: Run with Docker (easiest)

**Prerequisites:** Docker and Docker Compose installed.

1. **Open terminal in project root:**
   ```
   cd c:\Users\shiba\Downloads\ANMIR\network-monitoring-system
   ```

2. **Create env file (optional; defaults work for Docker):**
   ```powershell
   copy .env.example .env
   ```

3. **Start all services:**
   ```powershell
   cd docker
   docker-compose up -d
   ```
   Wait ~30 seconds for PostgreSQL and Redis to be ready.

4. **Seed sample data (102 nodes + metrics):**
   ```powershell
   cd ..
   docker exec nm-api python scripts/seed_nodes.py
   ```

5. **Verify it's working:**
   - **API health:** Open in browser: http://localhost:8000/health  
     You should see: `{"status":"ok","service":"Network Monitoring System"}`
   - **API docs:** http://localhost:8000/docs
   - **Dashboard:** http://localhost:3000  
     You should see the dashboard with nodes, stats, and charts.
   - **Nodes:** http://localhost:8000/api/v1/nodes  
     Should return a JSON list of nodes.

6. **Test simulation (optional):**  
   In the dashboard go to **Simulate**, enter e.g. `node-1`, click **Simulate latency spike**. Then check **Incidents** – a new incident may appear.

---

## Option B: Run locally (no Docker)

**Prerequisites:** Python 3.11+, PostgreSQL, Redis installed and running.

1. **Create database and user (in PostgreSQL):**
   ```sql
   CREATE USER monitor WITH PASSWORD 'monitor';
   CREATE DATABASE network_monitoring OWNER monitor;
   ```

2. **Terminal in project root:**
   ```powershell
   cd c:\Users\shiba\Downloads\ANMIR\network-monitoring-system
   ```

3. **Create virtual environment and install dependencies:**
   ```powershell
   python -m venv venv
   .\venv\Scripts\activate
   pip install -r requirements.txt
   ```

4. **Set environment (create `.env` from `.env.example`):**
   - `DATABASE_URL=postgresql://monitor:monitor@localhost:5432/network_monitoring`
   - `REDIS_URL=redis://localhost:6379/0`
   - `CELERY_BROKER_URL=redis://localhost:6379/1`

5. **Run the API:**
   ```powershell
   $env:PYTHONPATH = (Get-Location).Path
   uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
   ```
   Leave this terminal open.

6. **Seed data (new terminal, same folder, venv activated):**
   ```powershell
   $env:PYTHONPATH = (Get-Location).Path
   python scripts/seed_nodes.py
   ```

7. **Run the dashboard (new terminal):**
   ```powershell
   cd dashboard
   npm install
   $env:REACT_APP_API_URL = "http://localhost:8000"
   npm start
   ```
   Browser should open to http://localhost:3000.

8. **Verify:** Same as Option A (health, docs, dashboard, /api/v1/nodes).

---

## Quick “Is it working?” checklist

| Check | What to do | Expected |
|-------|------------|----------|
| API up | Open http://localhost:8000/health | `{"status":"ok",...}` |
| DB + seed | Open http://localhost:8000/api/v1/nodes | JSON array of nodes |
| Docs | Open http://localhost:8000/docs | Swagger UI |
| Dashboard | Open http://localhost:3000 | Dashboard with stats/charts |
| Simulate | Dashboard → Simulate → Simulate latency spike for `node-1` | “Latency spike simulated” |
| Incidents | Dashboard → Incidents | List (may show new incident after simulate) |

If all of the above work, the project is running and working.
