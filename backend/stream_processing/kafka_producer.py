"""
Kafka producer for metrics. Agents can send metrics to Kafka topic instead of or in addition to REST.
"""
import logging
import json
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


def produce_metric(payload: Dict[str, Any]) -> bool:
    """Send metric payload to Kafka metrics topic. Returns True if sent or Kafka disabled."""
    from backend.config import get_settings
    settings = get_settings()
    bootstrap = getattr(settings, "KAFKA_BOOTSTRAP_SERVERS", None) or ""
    if not bootstrap.strip():
        return False

    try:
        from kafka import KafkaProducer
    except ImportError:
        logger.warning("kafka-python not installed")
        return False

    try:
        producer = KafkaProducer(
            bootstrap_servers=bootstrap.split(","),
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )
        topic = getattr(settings, "KAFKA_METRICS_TOPIC", "network-metrics")
        producer.send(topic, value=payload)
        producer.flush()
        return True
    except Exception as e:
        logger.exception("Kafka produce error: %s", e)
        return False
