from fastapi import APIRouter
from pydantic import BaseModel

from app.agents.graph import run_agent_flow
from app.config import get_settings
from app.db.setup import ensure_database_ready

router = APIRouter(prefix="/api")


class ChatRequest(BaseModel):
    session_id: str
    message: str


@router.post("/chat")
def chat(request: ChatRequest) -> dict:
    settings = get_settings()
    conn = ensure_database_ready(settings.database_path)
    return run_agent_flow(conn, request.session_id, request.message)