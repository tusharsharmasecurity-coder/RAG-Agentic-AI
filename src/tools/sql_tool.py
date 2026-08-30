from langchain.tools import tool

from src.sql_engine import SQLEngine
from src.logger import log

_engine = None


def get_sql_engine():
    global _engine

    if _engine is None:
        _engine = SQLEngine()
        log("SQL_TOOL", "Initialized")

    return _engine


@tool
def sql_tool(question: str):
    """Execute SQL queries."""

    log("SQL_TOOL", f"Question: {question}")

    return get_sql_engine().ask(question)