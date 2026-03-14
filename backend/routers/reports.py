"""Reports API - daily AI report and PDF download."""
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.schemas import DailyReportResponse
from backend.reporting_service.generator import generate_daily_report
from database.session import get_sync_session
from database.models import DailyReport
import os

router = APIRouter(prefix="/reports", prefix_override="")


def get_db():
    db = get_sync_session()
    try:
        yield db
    finally:
        db.close()


@router.get("/daily", response_model=DailyReportResponse)
def get_daily_report(
    date: Optional[str] = None,
    regenerate: bool = False,
    db: Session = Depends(get_db),
):
    """Get or generate the daily network health report (AI summary + metrics). Optionally regenerate."""
    target = datetime.utcnow()
    if date:
        try:
            target = datetime.fromisoformat(date.replace("Z", "+00:00"))
        except ValueError:
            target = datetime.utcnow()
    start = target.replace(hour=0, minute=0, second=0, microsecond=0)

    existing = db.query(DailyReport).filter(DailyReport.report_date == start).first()
    if existing and not regenerate:
        return _to_response(existing)

    report = generate_daily_report(db, for_date=target)
    return _to_response(report)


@router.get("/daily/download")
def download_daily_report_pdf(
    date: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Download the daily report as PDF."""
    target = datetime.utcnow()
    if date:
        try:
            target = datetime.fromisoformat(date.replace("Z", "+00:00"))
        except ValueError:
            pass
    start = target.replace(hour=0, minute=0, second=0, microsecond=0)
    report = db.query(DailyReport).filter(DailyReport.report_date == start).first()
    if not report or not report.pdf_path or not os.path.isfile(report.pdf_path):
        # Generate once
        report = generate_daily_report(db, for_date=target)
    if report.pdf_path and os.path.isfile(report.pdf_path):
        return FileResponse(report.pdf_path, filename=os.path.basename(report.pdf_path), media_type="application/pdf")
    raise HTTPException(status_code=404, detail="PDF not available")


def _to_response(r: DailyReport) -> DailyReportResponse:
    return DailyReportResponse(
        id=r.id,
        report_date=r.report_date,
        total_incidents=r.total_incidents,
        affected_nodes_count=r.affected_nodes_count,
        avg_downtime_minutes=r.avg_downtime_minutes,
        remediation_success_rate=r.remediation_success_rate,
        network_health_score=r.network_health_score,
        ai_summary=r.ai_summary,
        pdf_path=r.pdf_path,
    )
