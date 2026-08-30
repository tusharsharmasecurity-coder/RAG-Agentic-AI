import streamlit as st

from src.agent import DelhiveryAgent
from src.dashboard import Dashboard
from src.analytics.dashboard_agent import DashboardAgent
from src.learner import LearningEngine


@st.cache_resource(show_spinner=False)
def get_agent() -> DelhiveryAgent:
    """
    Create the main Delhivery agent once.

    Streamlit reruns the script frequently. Without cache_resource,
    the complete agent/RAG/embedding stack can be reconstructed
    repeatedly.
    """

    print("[RESOURCE] Creating DelhiveryAgent")

    agent = DelhiveryAgent()

    print("[RESOURCE] DelhiveryAgent ready")

    return agent


@st.cache_resource(show_spinner=False)
def get_dashboard() -> Dashboard:
    """
    Create Dashboard once.
    """

    print("[RESOURCE] Creating Dashboard")

    dashboard = Dashboard()

    print("[RESOURCE] Dashboard ready")

    return dashboard


@st.cache_resource(show_spinner=False)
def get_dashboard_agent() -> DashboardAgent:
    """
    Create DashboardAgent once.
    """

    print("[RESOURCE] Creating DashboardAgent")

    dashboard_agent = DashboardAgent()

    print("[RESOURCE] DashboardAgent ready")

    return dashboard_agent


@st.cache_resource(show_spinner=False)
def get_learner() -> LearningEngine:
    """
    Create LearningEngine once.
    """

    print("[RESOURCE] Creating LearningEngine")

    learner = LearningEngine()

    print("[RESOURCE] LearningEngine ready")

    return learner