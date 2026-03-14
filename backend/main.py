"""FastAPI application entry point."""
from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import get_settings
from backend.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)
from backend.routers import (
    metrics,
    nodes,
    incidents,
    topology,
    reports,
    ai_chat,
    sla,
    simulation,
    predictions,
    root_cause,
    correlated,
    chaos,
)
from database.models import Base
from database import session as db_session

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure DB tables exist
    engine = db_session.get_engine(settings.DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    # Optional OpenTelemetry (set OTEL_EXPORTER_OTLP_ENDPOINT to enable)
    if getattr(settings, "OTEL_EXPORTER_OTLP_ENDPOINT", ""):
        try:
            from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
            FastAPIInstrumentor.instrument_app(app)
            logger.info("OpenTelemetry tracing enabled")
        except Exception as e:
            logger.warning("OpenTelemetry setup failed: %s", e)
    yield
    # Shutdown
    engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    description="AI-Powered Automated Network Monitoring and Self-Healing System",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(metrics.router, prefix=settings.API_PREFIX, tags=["Metrics"])
app.include_router(nodes.router, prefix=settings.API_PREFIX, tags=["Nodes"])
# Register /incidents/correlated and /incidents/{id}/root-cause before generic /incidents
app.include_router(correlated.router, prefix=settings.API_PREFIX, tags=["Event Correlation"])
app.include_router(root_cause.router, prefix=settings.API_PREFIX, tags=["Root Cause"])
app.include_router(incidents.router, prefix=settings.API_PREFIX, tags=["Incidents"])
app.include_router(topology.router, prefix=settings.API_PREFIX, tags=["Topology"])
app.include_router(reports.router, prefix=settings.API_PREFIX, tags=["Reports"])
app.include_router(ai_chat.router, prefix=settings.API_PREFIX, tags=["AI Chat"])
app.include_router(sla.router, prefix=settings.API_PREFIX, tags=["SLA"])
app.include_router(simulation.router, prefix=settings.API_PREFIX, tags=["Simulation"])
app.include_router(predictions.router, prefix=settings.API_PREFIX, tags=["Predictions"])
app.include_router(chaos.router, prefix=settings.API_PREFIX, tags=["Chaos Engineering"])


@app.get("/health")
def health():
    return {"status": "ok", "service": settings.APP_NAME}
