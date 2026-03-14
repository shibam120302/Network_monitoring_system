"""AI chat agent: answers questions about network state using DB + LLM."""
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from database.models import Node, Metric, Incident
from backend.config import get_settings


def answer_question(db: Session, question: str) -> tuple[str, list]:
    """Query DB for relevant data, build context, call LLM, return reply and optional sources."""
    q_lower = question.lower()
    context_parts = []
    sources = []

    # Which nodes are failing?
    if "failing" in q_lower or "down" in q_lower or "fail" in q_lower:
        incidents_open = (
            db.query(Incident, Node)
            .join(Node, Incident.node_id == Node.id)
            .filter(Incident.status.in_(["open", "investigating", "remediating"]))
            .order_by(desc(Incident.timestamp))
            .limit(20)
            .all()
        )
        if incidents_open:
            node_list = list({n.node_id for _, n in incidents_open})
            context_parts.append(f"Nodes with active incidents: {', '.join(node_list)}")
            sources.append("incidents (open)")
        else:
            context_parts.append("No nodes currently have open incidents.")

    # Why is node X down?
    if "why" in q_lower and "node" in q_lower:
        # Try to find node id in question (e.g. node-17)
        import re
        m = re.search(r"node-?\s*(\d+)", q_lower)
        if m:
            nid = f"node-{m.group(1)}"
            node = db.query(Node).filter(Node.node_id == nid).first()
            if node:
                inc = (
                    db.query(Incident)
                    .filter(Incident.node_id == node.id)
                    .order_by(desc(Incident.timestamp))
                    .first()
                )
                if inc:
                    context_parts.append(f"Latest incident for {nid}: {inc.issue_type}, severity {inc.severity}. Description: {inc.description or 'N/A'}. Root cause: {inc.root_cause or 'Under investigation'}.")
                    sources.append(f"incident {inc.incident_id}")
                else:
                    context_parts.append(f"No incidents found for {nid}. Node may be up.")

    # Incidents in the last 24 hours
    if "incident" in q_lower and ("24" in question or "last" in q_lower):
        since = datetime.utcnow() - timedelta(hours=24)
        incs = db.query(Incident).filter(Incident.timestamp >= since).order_by(desc(Incident.timestamp)).limit(50).all()
        summary = [f"{i.issue_type} on node_id={i.node_id} at {i.timestamp}" for i in incs]
        context_parts.append("Last 24h incidents: " + ("; ".join(summary) if summary else "None"))
        sources.append("incidents (24h)")

    # Highest latency node
    if "highest latency" in q_lower or "highest latency" in q_lower:
        subq = (
            db.query(Metric.node_id, func.max(Metric.timestamp).label("mt"))
            .group_by(Metric.node_id)
            .subquery()
        )
        latest_metrics = (
            db.query(Metric)
            .join(subq, (Metric.node_id == subq.c.node_id) & (Metric.timestamp == subq.c.mt))
            .filter(Metric.latency_ms.isnot(None))
            .order_by(desc(Metric.latency_ms))
            .limit(5)
            .all()
        )
        if latest_metrics:
            node_ids = [db.query(Node).get(m.node_id).node_id for m in latest_metrics if db.query(Node).get(m.node_id)]
            latencies = [m.latency_ms for m in latest_metrics]
            context_parts.append(f"Nodes with highest recent latency: {list(zip(node_ids, latencies))}")
            sources.append("metrics (latency)")
        else:
            context_parts.append("No latency data available.")

    context = "\n".join(context_parts) if context_parts else "No specific context retrieved. General network monitoring system."

    prompt = f"""You are a network operations assistant. Answer the user's question based ONLY on the following context. Be concise and professional.

Context:
{context}

User question: {question}

Answer:"""

    settings = get_settings()
    reply = ""
    if settings.OPENAI_API_KEY or (settings.USE_LOCAL_LLM and settings.LOCAL_LLM_BASE_URL):
        try:
            from openai import OpenAI
            client = OpenAI(
                api_key=settings.OPENAI_API_KEY or "ollama",
                base_url=settings.LOCAL_LLM_BASE_URL if settings.USE_LOCAL_LLM else None,
            )
            r = client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=400,
            )
            reply = (r.choices[0].message.content or "").strip()
        except Exception as e:
            reply = f"I couldn't reach the AI service. Here is the data we have: {context}. Error: {e}"
    else:
        reply = f"Based on the current data: {context}"

    return reply, sources
