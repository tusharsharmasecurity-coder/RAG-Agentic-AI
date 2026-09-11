import os
import requests
from langchain.tools import tool
from src.logger import log

# Set your deployed Google Apps Script URL here or in your .env file
APPS_SCRIPT_URL = os.getenv("GOOGLE_APPS_SCRIPT_URL", "YOUR_DEPLOYED_WEB_APP_URL_HERE")


@tool
def workspace_tool(action: str, query: str = "", sheet_id: str = "") -> dict:
    """
    Use this tool to interact with Google Workspace (Gmail and Google Sheets).
    
    Args:
        action: Either 'read_emails' or 'read_sheet'
        query: Search query for emails (e.g., 'SLA escalation', 'is:unread')
        sheet_id: The ID of the Google Sheet to read
    """
    if not APPS_SCRIPT_URL or "YOUR_DEPLOYED" in APPS_SCRIPT_URL:
        return {
            "status": "error",
            "message": "Google Apps Script URL is not configured in environment variables."
        }

    log("WORKSPACE_TOOL", f"Action: {action} | Query: {query}")

    params = {"action": action}
    if action == "read_emails":
        params["query"] = query if query else "label:unread"
    elif action == "read_sheet":
        params["sheet_id"] = sheet_id

    try:
        response = requests.get(APPS_SCRIPT_URL, params=params, timeout=15)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        log("WORKSPACE_TOOL", f"Error: {e}")
        return {"status": "error", "message": str(e)}