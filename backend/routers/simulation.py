"""Simulation API - inject artificial failures for testing."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.schemas import SimulateRequest, SimulateResponse
from backend.simulation.runner import (
    simulate_latency,
    simulate_packet_loss,
    simulate_link_failure,
    simulate_cpu_spike,
)
from database.session import get_sync_session

router = APIRouter(prefix="/simulate", prefix_override="")


def get_db():
    db = get_sync_session()
    try:
        yield db
    finally:
        db.close()


@router.post("/latency", response_model=SimulateResponse)
def simulate_latency_endpoint(req: SimulateRequest, db: Session = Depends(get_db)):
    ok = simulate_latency(db, req.node_id, latency_ms=250)
    return SimulateResponse(success=ok, message="Latency spike simulated" if ok else "Failed")


@router.post("/packet_loss", response_model=SimulateResponse)
def simulate_packet_loss_endpoint(req: SimulateRequest, db: Session = Depends(get_db)):
    ok = simulate_packet_loss(db, req.node_id, packet_loss_pct=12)
    return SimulateResponse(success=ok, message="Packet loss simulated" if ok else "Failed")


@router.post("/link_failure", response_model=SimulateResponse)
def simulate_link_failure_endpoint(req: SimulateRequest, db: Session = Depends(get_db)):
    ok = simulate_link_failure(db, req.node_id)
    return SimulateResponse(success=ok, message="Link failure simulated" if ok else "Failed")


@router.post("/cpu_spike", response_model=SimulateResponse)
def simulate_cpu_spike_endpoint(req: SimulateRequest, db: Session = Depends(get_db)):
    ok = simulate_cpu_spike(db, req.node_id, cpu_pct=95)
    return SimulateResponse(success=ok, message="CPU spike simulated" if ok else "Failed")
