"""Daily AI report generation and PDF export. Includes predictions, correlated incidents, root cause, chaos results."""
from datetime import datetime, timedelta
from io import BytesIO
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from database.models import (
    Incident,
    Node,
    RemediationLog,
    DailyReport,
    FailurePrediction,
    IncidentCorrelationGroup,
    ChaosSimulationRun,
)
from backend.config import get_settings


def generate_daily_report(db: Session, for_date: datetime = None) -> DailyReport:
    """Aggregate stats for the day, generate AI summary, optionally PDF; save DailyReport."""
    for_date = for_date or datetime.utcnow()
    start = for_date.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)

    incidents = (
        db.query(Incident)
        .filter(and_(Incident.timestamp >= start, Incident.timestamp < end))
        .all()
    )
    total = len(incidents)
    affected_ids = set(i.node_id for i in incidents)
    affected_count = len(affected_ids)

    # Avg downtime: from resolved_at - timestamp for resolved
    resolved = [i for i in incidents if i.resolved_at]
    avg_downtime = None
    if resolved:
        total_mins = sum((i.resolved_at - i.timestamp).total_seconds() / 60 for i in resolved)
        avg_downtime = total_mins / len(resolved)

    # Remediation success rate
    remed_count = db.query(RemediationLog).filter(
        RemediationLog.executed_at >= start,
        RemediationLog.executed_at < end,
    ).count()
    success_count = db.query(RemediationLog).filter(
        RemediationLog.executed_at >= start,
        RemediationLog.executed_at < end,
        RemediationLog.success == True,
    ).count()
    remediation_success_rate = (success_count / remed_count * 100) if remed_count else None

    # Health score 0-100 (simplified: fewer incidents = higher)
    total_nodes = db.query(Node).filter(Node.is_active == True).count()
    health_score = 100.0
    if total_nodes:
        health_score = max(0, 100 - (affected_count / total_nodes * 100) - total * 2)

    root_causes = {}
    for i in incidents:
        t = i.issue_type
        root_causes[t] = root_causes.get(t, 0) + 1

    # Extended sections: predictions, correlated, root cause summaries, chaos results
    since = start
    predictions_high = db.query(FailurePrediction).filter(
        FailurePrediction.computed_at >= since,
        FailurePrediction.failure_probability >= 0.5,
    ).count()
    correlated_groups = db.query(IncidentCorrelationGroup).filter(
        IncidentCorrelationGroup.created_at >= since,
    ).count()
    chaos_runs = db.query(ChaosSimulationRun).filter(
        ChaosSimulationRun.started_at >= since,
    ).all()
    chaos_detected = sum(1 for r in chaos_runs if r.detection_verified)
    chaos_remediated = sum(1 for r in chaos_runs if r.remediation_verified)

    ai_summary = _generate_ai_summary(
        total_incidents=total,
        affected_count=affected_count,
        total_nodes=total_nodes,
        avg_downtime_minutes=avg_downtime,
        remediation_success_rate=remediation_success_rate,
        root_causes=root_causes,
        health_score=health_score,
        predictions_high=predictions_high,
        correlated_groups=correlated_groups,
        chaos_runs=len(chaos_runs),
        chaos_detection_rate=(chaos_detected / len(chaos_runs) * 100) if chaos_runs else None,
        chaos_remediation_rate=(chaos_remediated / len(chaos_runs) * 100) if chaos_runs else None,
    )

    report = DailyReport(
        report_date=start,
        total_incidents=total,
        affected_nodes_count=affected_count,
        avg_downtime_minutes=avg_downtime,
        remediation_success_rate=remediation_success_rate,
        network_health_score=health_score,
        ai_summary=ai_summary,
        root_causes_json=root_causes,
    )
    db.add(report)
    db.flush()

    # PDF (with extended sections)
    pdf_buffer = _generate_pdf(
        report,
        ai_summary,
        root_causes,
        avg_downtime,
        remediation_success_rate,
        health_score,
        predictions_high=predictions_high,
        correlated_groups=correlated_groups,
        chaos_runs=len(chaos_runs),
        chaos_detection_rate=(chaos_detected / len(chaos_runs) * 100) if chaos_runs else None,
        chaos_remediation_rate=(chaos_remediated / len(chaos_runs) * 100) if chaos_runs else None,
    )
    if pdf_buffer:
        import os
        reports_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "reports")
        os.makedirs(reports_dir, exist_ok=True)
        path = os.path.join(reports_dir, f"daily_report_{start.date()}.pdf")
        with open(path, "wb") as f:
            f.write(pdf_buffer.getvalue())
        report.pdf_path = path
    db.commit()
    db.refresh(report)
    return report


def _generate_ai_summary(
    total_incidents: int,
    affected_count: int,
    total_nodes: int,
    avg_downtime_minutes: float | None,
    remediation_success_rate: float | None,
    root_causes: dict,
    health_score: float,
    predictions_high: int = 0,
    correlated_groups: int = 0,
    chaos_runs: int = 0,
    chaos_detection_rate: float | None = None,
    chaos_remediation_rate: float | None = None,
) -> str:
    """Call OpenAI or local LLM to generate 1-page summary including predictions, correlated incidents, chaos results."""
    settings = get_settings()
    prompt = f"""Generate a concise 1-paragraph network health report summary (2-4 sentences) for the last 24 hours.
Total incidents: {total_incidents}
Affected nodes: {affected_count} out of {total_nodes}
Average downtime (minutes): {avg_downtime_minutes}
Remediation success rate (%): {remediation_success_rate}
Root causes breakdown: {root_causes}
Network health score (0-100): {health_score}
Predicted high-risk nodes (failure probability >= 50%): {predictions_high}
Correlated incident groups (alerts grouped): {correlated_groups}
Chaos engineering runs: {chaos_runs}; detection rate: {chaos_detection_rate}%; remediation rate: {chaos_remediation_rate}%
Write in professional tone. Mention key figures, the most common issue, and if relevant predicted failures or chaos test results."""

    if settings.OPENAI_API_KEY:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            base_url = None
            if settings.USE_LOCAL_LLM and settings.LOCAL_LLM_BASE_URL:
                base_url = settings.LOCAL_LLM_BASE_URL
            if base_url:
                client = OpenAI(base_url=base_url, api_key="ollama")
            r = client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
            )
            return (r.choices[0].message.content or "").strip()
        except Exception:
            pass

    # Fallback template
    top_cause = max(root_causes, key=root_causes.get) if root_causes else "N/A"
    extra = ""
    if predictions_high:
        extra += f" {predictions_high} node(s) had high failure probability. "
    if correlated_groups:
        extra += f" {correlated_groups} correlated incident groups were identified. "
    if chaos_runs and chaos_detection_rate is not None:
        extra += f" Chaos tests: {chaos_detection_rate:.0f}% detection, {chaos_remediation_rate or 0:.0f}% remediation. "
    return (
        f"During the last 24 hours the monitoring system detected {total_incidents} incidents across {total_nodes} nodes. "
        f"The most common issue was {top_cause}. "
        f"Automated remediation resolved {remediation_success_rate or 0:.0f}% of incidents without manual intervention. "
        f"Network health score: {health_score:.0f}/100.{extra}"
    )


def _generate_pdf(
    report,
    ai_summary: str,
    root_causes: dict,
    avg_downtime,
    remediation_success_rate,
    health_score,
    predictions_high: int = 0,
    correlated_groups: int = 0,
    chaos_runs: int = 0,
    chaos_detection_rate: float | None = None,
    chaos_remediation_rate: float | None = None,
) -> BytesIO | None:
    """Generate PDF with reportlab including predictions, correlated, chaos results."""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib import colors
        from reportlab.lib.units import inch

        buf = BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
        styles = getSampleStyleSheet()
        story = []
        story.append(Paragraph("Network Health Report - Daily Summary", styles["Title"]))
        story.append(Spacer(1, 0.25 * inch))
        story.append(Paragraph(f"Report Date: {report.report_date.date()}", styles["Normal"]))
        story.append(Spacer(1, 0.2 * inch))
        story.append(Paragraph("Summary", styles["Heading2"]))
        story.append(Paragraph(ai_summary, styles["Normal"]))
        story.append(Spacer(1, 0.2 * inch))
        data = [
            ["Metric", "Value"],
            ["Total Incidents", str(report.total_incidents)],
            ["Affected Nodes", str(report.affected_nodes_count)],
            ["Avg Downtime (min)", f"{avg_downtime:.1f}" if avg_downtime else "N/A"],
            ["Remediation Success Rate (%)", f"{remediation_success_rate:.1f}" if remediation_success_rate else "N/A"],
            ["Network Health Score", f"{health_score:.0f}/100"],
            ["High-Risk Predictions", str(predictions_high)],
            ["Correlated Incident Groups", str(correlated_groups)],
            ["Chaos Runs", str(chaos_runs)],
            ["Chaos Detection Rate (%)", f"{chaos_detection_rate:.1f}" if chaos_detection_rate is not None else "N/A"],
            ["Chaos Remediation Rate (%)", f"{chaos_remediation_rate:.1f}" if chaos_remediation_rate is not None else "N/A"],
        ]
        t = Table(data)
        t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.grey), ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke)]))
        story.append(t)
        story.append(Spacer(1, 0.2 * inch))
        story.append(Paragraph("Root Causes", styles["Heading2"]))
        rc_data = [["Issue Type", "Count"]] + [[k, str(v)] for k, v in root_causes.items()]
        if len(rc_data) == 1:
            rc_data.append(["None", "-"])
        t2 = Table(rc_data)
        story.append(t2)
        doc.build(story)
        buf.seek(0)
        return buf
    except Exception:
        return None
