"""
Kafka consumer for metrics stream. Consumes from metrics topic, runs anomaly detection,
and persists to PostgreSQL. Optional: when KAFKA_BOOTSTRAP_SERVERS is not set, REST ingestion is used only.
"""
import logging
import json
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


def run_consumer_loop():
    """
    Run Kafka consumer loop: poll metrics topic, parse payload, call metric ingestion + anomaly check.
    Designed to be run in a Celery task or background thread.
    """
    from backend.config import get_settings
    settings = get_settings()
    bootstrap = getattr(settings, "KAFKA_BOOTSTRAP_SERVERS", None) or ""
    if not bootstrap.strip():
        logger.info("KAFKA_BOOTSTRAP_SERVERS not set; stream consumer disabled")
        return

    try:
        from kafka import KafkaConsumer
    except ImportError:
        logger.warning("kafka-python not installed; stream consumer disabled")
        return

    topic = getattr(settings, "KAFKA_METRICS_TOPIC", "network-metrics")
    consumer = KafkaConsumer(
        topic,
        bootstrap_servers=bootstrap.split(","),
        value_deserializer=lambda m: json.loads(m.decode("utf-8")) if m else None,
        auto_offset_reset="latest",
    )

    from database.session import get_sync_session
    from database.models import Node, Metric
    from backend.incident_engine.detector import check_metrics_and_create_incident

    for message in consumer:
        try:
            payload = message.value
            if not payload or "node_id" not in payload:
                continue
            db = get_sync_session()
            try:
                node = db.query(Node).filter(Node.node_id == payload["node_id"]).first()
                if not node:
                    node = Node(node_id=payload["node_id"], hostname=payload["node_id"])
                    db.add(node)
                    db.commit()
                    db.refresh(node)
                ts = datetime.fromisoformat(payload.get("timestamp", datetime.utcnow().isoformat()).replace("Z", "+00:00")) if isinstance(payload.get("timestamp"), str) else datetime.utcnow()
                metric = Metric(
                    node_id=node.id,
                    latency_ms=payload.get("latency"),
                    packet_loss_pct=payload.get("packet_loss"),
                    cpu_usage_pct=payload.get("cpu_usage"),
                    memory_usage_pct=payload.get("memory_usage"),
                    interface_status=payload.get("interface_status"),
                    bandwidth_usage_mbps=payload.get("bandwidth_usage"),
                    timestamp=ts,
                    raw_payload=payload,
                )
                db.add(metric)
                db.commit()
                db.refresh(metric)
                check_metrics_and_create_incident(db, metric, node)
                db.commit()
            finally:
                db.close()
        except Exception as e:
            logger.exception("Stream processing error: %s", e)
