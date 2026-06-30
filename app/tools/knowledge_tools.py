from app.config import Settings


def adapt_mcp_text_to_snippets(text: str) -> dict:
    if not text.strip():
        return {"snippets": [], "raw_mcp_response": {"text": text}}
    return {
        "snippets": [
            {
                "title": "RAG 检索结果",
                "policy_type": "unknown",
                "content": text,
                "source": "mcp:query_knowledge_hub",
                "score": None,
            }
        ],
        "raw_mcp_response": {"text": text},
    }


class KnowledgeTools:
    def __init__(self, settings: Settings):
        self.settings = settings

    async def search(self, query: str, collection: str | None = None, top_k: int = 5) -> dict:
        # V1 keeps the external MCP call behind this seam. If the server is not
        # available during local tests, return no snippets rather than fabricate policy.
        return {"snippets": [], "raw_mcp_response": {"query": query, "collection": collection or self.settings.rag_mcp_collection, "top_k": top_k}}