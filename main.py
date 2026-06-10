import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.config import get_config

from starlette.responses import HTMLResponse
from starlette.routing import Route

from greennode_agentbase import GreenNodeAgentBaseApp, PingStatus, RequestContext
from greennode_agentbase.memory import MemoryClient
from greennode_agentbase.memory.models import MemoryRecordSearchRequest
from greennode_agent_bridge import AgentBaseMemoryEvents

from src.interview_tools import get_question, list_topics

load_dotenv()

app = GreenNodeAgentBaseApp()

MEMORY_ID = os.environ.get("MEMORY_ID", "")
if not MEMORY_ID:
    raise ValueError("MEMORY_ID environment variable is required for memory-enabled agents")

MEMORY_STRATEGY_ID = os.environ.get("MEMORY_STRATEGY_ID", "default")

checkpointer = AgentBaseMemoryEvents(memory_id=MEMORY_ID)
memory_client = MemoryClient()

LLM_MODEL = os.environ.get("LLM_MODEL", "")
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "")
LLM_API_KEY = os.environ.get("LLM_API_KEY", "")
if not LLM_MODEL or not LLM_BASE_URL or not LLM_API_KEY:
    raise ValueError(
        "LLM_MODEL, LLM_BASE_URL, and LLM_API_KEY environment variables are required. "
        "Set them in your .env file or use /agentbase-llm to get a platform API key."
    )

llm = ChatOpenAI(
    model=LLM_MODEL,
    base_url=LLM_BASE_URL,
    api_key=LLM_API_KEY,
)

PROMPT_PATH = Path(__file__).resolve().parent / "prompts" / "interviewer_system.md"
CHAT_UI_PATH = Path(__file__).resolve().parent / "static" / "chat.html"


async def chat_ui(_request):
    return HTMLResponse(CHAT_UI_PATH.read_text(encoding="utf-8"))


app.routes.insert(0, Route("/", chat_ui, methods=["GET"]))
app.routes.insert(1, Route("/chat", chat_ui, methods=["GET"]))


def _load_system_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


def _get_actor_id() -> str:
    config = get_config()
    return config["configurable"].get("actor_id", "default")


def _build_namespace(actor_id: str) -> str:
    return f"/strategies/{MEMORY_STRATEGY_ID}/actors/{actor_id}"


@tool
def remember(fact: str) -> str:
    """Store a fact about the candidate in long-term memory for later sessions.

    Args:
        fact: Observation to remember (e.g. weak area, strength, score summary).
    """
    namespace = _build_namespace(_get_actor_id())
    memory_client.insert_memory_records_directly(
        id=MEMORY_ID,
        namespace=namespace,
        request=[fact],
    )
    return f"Remembered: {fact}"


@tool
def recall(query: str) -> str:
    """Search long-term memory for prior notes about this candidate.

    Args:
        query: Natural language search query.
    """
    namespace = _build_namespace(_get_actor_id())
    results = memory_client.search_memory_records(
        id=MEMORY_ID,
        namespace=namespace,
        request=MemoryRecordSearchRequest(query=query, limit=10),
    )
    if not results:
        return "No relevant memories found."
    return "\n".join(f"- {r.memory} (score: {r.score:.2f})" for r in results)


agent = create_agent(
    llm,
    tools=[list_topics, get_question, remember, recall],
    system_prompt=_load_system_prompt(),
    checkpointer=checkpointer,
)


@app.entrypoint
def handler(payload: dict, context: RequestContext) -> dict:
    """Technical interviewer agent entrypoint."""
    if not context.user_id or not context.session_id:
        return {
            "status": "error",
            "error": (
                "Missing required headers: X-GreenNode-AgentBase-User-Id and "
                "X-GreenNode-AgentBase-Session-Id are required when using memory."
            ),
        }

    message = payload.get("message", "Hello")

    config = {
        "configurable": {
            "thread_id": context.session_id,
            "actor_id": context.user_id,
        }
    }

    result = agent.invoke(
        {"messages": [{"role": "user", "content": message}]},
        config=config,
    )
    ai_message = result["messages"][-1]
    return {
        "status": "success",
        "response": ai_message.content,
        "timestamp": datetime.now().isoformat(),
    }


@app.ping
def health_check() -> PingStatus:
    return PingStatus.HEALTHY


if __name__ == "__main__":
    app.run(port=8080, host="0.0.0.0")
