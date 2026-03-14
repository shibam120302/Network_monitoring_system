"""Pydantic schemas for API."""
from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, Field


# --- Metrics ---
class MetricPayload(BaseModel):
    node_id: str
    latency: Optional[float] = None
    packet_loss: Optional[float] = None
    cpu_usage: Optional[float] = None
    memory_usage: Optional[float] = None
    interface_status: Optional[str] = None
    bandwidth_usage: Optional[float] = None
    timestamp: Optional[datetime] = None

    class Config:
        from_attributes = True


class MetricResponse(BaseModel):
    id: int
    node_id: int
    latency_ms: Optional[float]
    packet_loss_pct: Optional[float]
    cpu_usage_pct: Optional[float]
    memory_usage_pct: Optional[float]
    interface_status: Optional[str]
    bandwidth_usage_mbps: Optional[float]
    timestamp: datetime

    class Config:
        from_attributes = True


# --- Nodes ---
class NodeCreate(BaseModel):
    node_id: str
    hostname: Optional[str] = None
    ip_address: Optional[str] = None
    device_type: Optional[str] = None
    snmp_community: Optional[str] = None


class NodeResponse(BaseModel):
    id: int
    node_id: str
    hostname: Optional[str]
    ip_address: Optional[str]
    device_type: Optional[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class NodeWithMetrics(NodeResponse):
    latest_latency: Optional[float] = None
    latest_packet_loss: Optional[float] = None
    latest_cpu: Optional[float] = None
    status: Optional[str] = "unknown"


# --- Incidents ---
class IncidentResponse(BaseModel):
    id: int
    incident_id: str
    node_id: int
    node_node_id: Optional[str] = None  # human-readable e.g. node-23
    issue_type: str
    severity: str
    status: str
    timestamp: datetime
    resolved_at: Optional[datetime]
    root_cause: Optional[str]
    description: Optional[str]

    class Config:
        from_attributes = True


class IncidentTimelineEventResponse(BaseModel):
    id: int
    event_time: datetime
    event_type: str
    message: Optional[str]

    class Config:
        from_attributes = True


class IncidentDetailResponse(IncidentResponse):
    timeline: List[IncidentTimelineEventResponse] = []
    node_node_id: Optional[str] = None


# --- Topology ---
class TopologyNode(BaseModel):
    id: str
    label: str
    status: str = "unknown"
    ip: Optional[str] = None


class TopologyEdge(BaseModel):
    source: str
    target: str
    bandwidth_mbps: Optional[float] = None
    is_up: bool = True


class TopologyResponse(BaseModel):
    nodes: List[TopologyNode]
    edges: List[TopologyEdge]
    graph_json: Optional[dict] = None


# --- Reports ---
class DailyReportResponse(BaseModel):
    id: int
    report_date: datetime
    total_incidents: int
    affected_nodes_count: int
    avg_downtime_minutes: Optional[float]
    remediation_success_rate: Optional[float]
    network_health_score: Optional[float]
    ai_summary: Optional[str]
    pdf_path: Optional[str]

    class Config:
        from_attributes = True


# --- AI Chat ---
class ChatRequest(BaseModel):
    message: str
    context: Optional[dict] = None


class ChatResponse(BaseModel):
    reply: str
    sources: Optional[List[str]] = None


# --- SLA ---
class SLAResponse(BaseModel):
    node_id: Optional[int]
    node_node_id: Optional[str]
    period_start: datetime
    period_end: datetime
    uptime_pct: Optional[float]
    mttr_minutes: Optional[float]
    mtbf_minutes: Optional[float]
    incident_count: int

    class Config:
        from_attributes = True


# --- Simulation ---
class SimulateRequest(BaseModel):
    node_id: str
    duration_seconds: Optional[int] = 60


class SimulateResponse(BaseModel):
    success: bool
    message: str
    simulation_id: Optional[str] = None


# --- Feature 1: Predictions ---
class PredictionResponse(BaseModel):
    node_id: str
    failure_probability: float
    predicted_issue: Optional[str] = None


# --- Feature 2: Root cause ---
class RootCauseResponse(BaseModel):
    incident_id: str
    root_cause: str
    affected_nodes: List[str]
    analysis_time: Optional[str] = None


# --- Feature 3: Correlated incidents ---
class CorrelatedGroupResponse(BaseModel):
    group_id: int
    root_cause_summary: Optional[str] = None
    created_at: Optional[str] = None
    incident_ids: List[str]
    affected_nodes: List[str]


# --- Feature 5: Chaos ---
class ChaosSimulateRequest(BaseModel):
    node_id: str
    failure_type: str  # packet_loss, high_latency, cpu_spike, link_failure, node_shutdown
    duration_seconds: Optional[int] = 120


class ChaosSimulateResponse(BaseModel):
    success: bool
    run_id: Optional[int] = None
    detection_verified: Optional[bool] = None
    remediation_verified: Optional[bool] = None
    message: str
