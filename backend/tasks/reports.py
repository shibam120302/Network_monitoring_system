"""Celery tasks: daily report generation."""
from backend.celery_app import app
from database.session import get_sync_session
from backend.reporting_service.generator import generate_daily_report


@app.task(bind=True)
def generate_daily_report_task(self):
    """Generate and store daily AI report."""
    db = get_sync_session()
    try:
        report = generate_daily_report(db)
        return {"report_id": report.id, "report_date": str(report.report_date)}
    finally:
        db.close()
