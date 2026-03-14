"""SQLAlchemy models for network monitoring."""
from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    DateTime,
    Text,
    ForeignKey,
    Enum as SQLEnum,
    Index,
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
import enum

Base = declarative_base()


class BaseMixin(Base):
    __abstract__ = True
    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# --- Enums ---
class IncidentStatus(str, enum.Enum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    REMEDIATING = "remediating"
    RESOLVED = "resolved"
    CLOSED = "closed"


class IncidentSeverity(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RemediationAction(str, enum.Enum):
    RESTART_INTERFACE = "restart_interface"
    RESTART_AGENT = "restart_agent"
    REROUTE_TRAFFIC = "reroute_traffic"
    RESTART_SERVICE = "restart_service"
    RESTART_PROCESS = "restart_process"
    NONE = "none"


# --- Tables ---
class Node(BaseMixin):
    __tablename__ = "nodes"

    node_id = Column(String(64), unique=True, nullable=False, index=True)  # e.g. node-23
    hostname = Column(String(256), nullable=True)
    ip_address = Column(String(45), nullable=True)
    device_type = Column(String(64), nullable=True)  # cisco_ios, etc.
    snmp_community = Column(String(128), nullable=True)
    is_active = Column(Boolean, default=True)
    metadata_ = Column("metadata", JSONB, default=dict)

    metrics = relationship("Metric", back_populates="node", cascade="all, delete-orphan")
    incidents = relationship("Incident", back_populates="node", cascade="all, delete-orphan")
    topology_links = relationship("TopologyLink", foreign_keys="TopologyLink.source_node_id", back_populates="source_node")

    def __repr__(self):
        return f"<Node {self.node_id}>"


class Metric(BaseMixin):
    __tablename__ = "metrics"

    node_id = Column(Integer, ForeignKey("nodes.id"), nullable=False, index=True)
    latency_ms = Column(Float, nullable=True)
    packet_loss_pct = Column(Float, nullable=True)
    cpu_usage_pct = Column(Float, nullable=True)
    memory_usage_pct = Column(Float, nullable=True)
    interface_status = Column(String(32), nullable=True)  # up, down
    bandwidth_usage_mbps = Column(Float, nullable=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    raw_payload = Column(JSONB, nullable=True)

    node = relationship("Node", back_populates="metrics")

    __table_args__ = (Index("ix_metrics_node_timestamp", "node_id", "timestamp"),)


class Incident(BaseMixin):
    __tablename__ = "incidents"

    incident_id = Column(String(64), unique=True, nullable=False, index=True)
    node_id = Column(Integer, ForeignKey("nodes.id"), nullable=False, index=True)
    issue_type = Column(String(128), nullable=False)
    severity = Column(SQLEnum(IncidentSeverity), default=IncidentSeverity.MEDIUM)
    status = Column(SQLEnum(IncidentStatus), default=IncidentStatus.OPEN)
    timestamp = Column(DateTime, nullable=False, index=True)
    resolved_at = Column(DateTime, nullable=True)
    root_cause = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    metric_snapshot = Column(JSONB, nullable=True)

    node = relationship("Node", back_populates="incidents")
    timeline_events = relationship("IncidentTimelineEvent", back_populates="incident", cascade="all, delete-orphan")
    remediation_logs = relationship("RemediationLog", back_populates="incident", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Incident {self.incident_id} {self.issue_type}>"


class IncidentTimelineEvent(BaseMixin):
    __tablename__ = "incident_timeline_events"

    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=False, index=True)
    event_time = Column(DateTime, nullable=False)
    event_type = Column(String(64), nullable=False)  # detected, created, remediation_triggered, resolved
    message = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSONB, default=dict)

    incident = relationship("Incident", back_populates="timeline_events")


class RemediationLog(BaseMixin):
    __tablename__ = "remediation_logs"

    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=False, index=True)
    action = Column(String(128), nullable=False)
    command_executed = Column(Text, nullable=True)
    success = Column(Boolean, nullable=False)
    output = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    executed_at = Column(DateTime, nullable=False)

    incident = relationship("Incident", back_populates="remediation_logs")


class TopologyLink(BaseMixin):
    __tablename__ = "topology_links"

    source_node_id = Column(Integer, ForeignKey("nodes.id"), nullable=False, index=True)
    target_node_id = Column(Integer, ForeignKey("nodes.id"), nullable=False, index=True)
    link_name = Column(String(128), nullable=True)
    bandwidth_mbps = Column(Float, nullable=True)
    is_up = Column(Boolean, default=True)

    source_node = relationship("Node", foreign_keys=[source_node_id], back_populates="topology_links")
    target_node = relationship("Node", foreign_keys=[target_node_id])


class DailyReport(BaseMixin):
    __tablename__ = "daily_reports"

    report_date = Column(DateTime, nullable=False, index=True)
    total_incidents = Column(Integer, default=0)
    affected_nodes_count = Column(Integer, default=0)
    avg_downtime_minutes = Column(Float, nullable=True)
    remediation_success_rate = Column(Float, nullable=True)
    network_health_score = Column(Float, nullable=True)  # 0-100
    ai_summary = Column(Text, nullable=True)
    root_causes_json = Column(JSONB, nullable=True)
    pdf_path = Column(String(512), nullable=True)


class SLAMetrics(BaseMixin):
    __tablename__ = "sla_metrics"

    node_id = Column(Integer, ForeignKey("nodes.id"), nullable=True, index=True)  # null = global
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    uptime_pct = Column(Float, nullable=True)
    mttr_minutes = Column(Float, nullable=True)  # Mean Time To Recovery
    mtbf_minutes = Column(Float, nullable=True)  # Mean Time Between Failures
    incident_count = Column(Integer, default=0)
