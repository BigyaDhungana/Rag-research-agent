from app.agent.tools.search_web import search_web
from app.agent.tools.fetch_page import fetch_page
from app.agent.tools.search_documents import search_documents

TOOL_REGISTRY = {
    "search_web": search_web,
    "fetch_page": fetch_page,
    "search_documents": search_documents,
}