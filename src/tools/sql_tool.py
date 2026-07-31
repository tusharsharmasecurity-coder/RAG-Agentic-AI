from langchain.tools import tool

from src.sql_engine import SQLEngine
from src.logger import log

engine = SQLEngine()

log("SQL_TOOL", "Initialized")


@tool
def sql_tool(question: str):
    """Execute SQL queries."""

    log("SQL_TOOL", f"Question: {question}")

    return engine.ask(question)