from pathlib import Path
import os

from pydantic import BaseModel


class Settings(BaseModel):
    database_path: Path = Path(os.getenv("APP_DATABASE_PATH", "data/app.db"))
    rag_mcp_server_path: Path = Path(os.getenv("RAG_MCP_SERVER_PATH", r"D:\dev\MODULAR-RAG-MCP-SERVER"))
    rag_mcp_start_command: str = os.getenv("RAG_MCP_START_COMMAND", "python -m src.mcp_server.server")
    rag_mcp_collection: str = os.getenv("RAG_MCP_COLLECTION", "ecommerce_qa")
    rag_mcp_query_tool: str = os.getenv("RAG_MCP_QUERY_TOOL", "query_knowledge_hub")
    rag_mcp_timeout_seconds: float = float(os.getenv("RAG_MCP_TIMEOUT_SECONDS", "30"))


def get_settings() -> Settings:
    return Settings()