"""AI Chat API."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.schemas import ChatRequest, ChatResponse
from backend.ai_agent.chat import answer_question
from database.session import get_sync_session

router = APIRouter(prefix="/ai", prefix_override="")


def get_db():
    db = get_sync_session()
    try:
        yield db
    finally:
        db.close()


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, db: Session = Depends(get_db)):
    """Ask the AI agent a question about the network. Returns natural language answer."""
    reply, sources = answer_question(db, request.message)
    return ChatResponse(reply=reply, sources=sources)
