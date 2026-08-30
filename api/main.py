from fastapi import FastAPI
from pydantic import BaseModel

from src.agent import DelhiveryAgent

app = FastAPI(
    title="Delhivery Agentic AI API",
    version="1.0.0",
)

agent = DelhiveryAgent()


class QueryRequest(BaseModel):
    question: str


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "delhivery-agentic-ai",
    }


@app.post("/ask")
def ask(request: QueryRequest):
    result = agent.ask(request.question)

    return {
        "question": request.question,
        "result": result,
    }


@app.get("/metrics")
def metrics():
    return agent.metrics.summary()
