"""Celery tasks: run agent collection for multiple nodes."""
from backend.celery_app import app
from backend.config import get_settings
from backend.agents.collector import collect_metrics, send_metrics


@app.task(bind=True)
def collect_and_send_metrics(self, node_id: str, target_host: str = None):
    """Collect metrics for one node and POST to central API."""
    settings = get_settings()
    payload = collect_metrics(
        node_id,
        target_host=target_host,
        device_type=settings.NETMIKO_DEVICE_TYPE,
    )
    api_base = settings.CENTRAL_API_URL
    ok = send_metrics(api_base, payload)
    return {"node_id": node_id, "ok": ok}
