import asyncio

from app.tools.knowledge_tools import KnowledgeTools


def knowledge_qa_node(state: dict, knowledge_tools: KnowledgeTools) -> dict:
    try:
        result = asyncio.run(knowledge_tools.search(state["user_message"]))
    except RuntimeError:
        loop = asyncio.new_event_loop()
        try:
            result = loop.run_until_complete(knowledge_tools.search(state["user_message"]))
        finally:
            loop.close()
    except Exception as exc:
        result = {"snippets": [], "error": str(exc)}
    state["knowledge_snippets"] = result.get("snippets", [])
    state.setdefault("trace_steps", []).append({
        "agent_name": "KnowledgeQAAgent",
        "intent": state.get("intent"),
        "tool_name": "knowledge.search",
        "tool_output_summary": f"检索到 {len(state['knowledge_snippets'])} 条知识片段",
        "decision_reason": "用户问题属于规则、政策或流程问答",
    })
    return state