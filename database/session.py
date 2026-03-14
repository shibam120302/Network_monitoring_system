"""Database session and engine setup."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from database.models import Base, Node, Metric, Incident, IncidentTimelineEvent, RemediationLog, TopologyLink, DailyReport, SLAMetrics  # noqa: F401

# Sync engine for Celery/agents
def get_engine(database_url: str):
    from backend.config import get_settings
    url = database_url or get_settings().DATABASE_URL
    return create_engine(url, pool_pre_ping=True, pool_size=10, max_overflow=20)

def get_session_factory(database_url: str = None):
    engine = get_engine(database_url or "")
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_sync_session() -> Session:
    from backend.config import get_settings
    factory = get_session_factory(get_settings().DATABASE_URL)
    return factory()
