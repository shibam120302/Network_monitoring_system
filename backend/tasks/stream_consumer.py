"""Celery task: run Kafka metrics consumer loop (optional)."""
from backend.celery_app import app
from backend.stream_processing.kafka_consumer import run_consumer_loop


@app.task(bind=True)
def run_kafka_consumer_task(self):
    """Run the Kafka consumer loop. Call once and let it run (e.g. from a dedicated worker)."""
    run_consumer_loop()
