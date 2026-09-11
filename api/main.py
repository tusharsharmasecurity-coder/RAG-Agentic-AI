import time
import asyncio
import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"
import shutil
from decimal import Decimal
from datetime import date, datetime
from typing import Optional, Any
from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel, Field
from fastapi import UploadFile, File, HTTPException
from src.upload.pdf_processor import ingest_pdf_to_faiss
from src.agent import DelhiveryAgent

app = FastAPI(
    title="Delhivery Agentic AI API",
    version="2.0.0",
    description="Enterprise API for logistics intelligence.",
)

# Initialize agent once at startup
agent = DelhiveryAgent()

# Create the storage directory for uploaded PDFs
UPLOAD_DIR = "data/documents"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def sanitize_for_json(obj: Any) -> Any:
    """
    Recursively converts non-JSON-serializable MySQL objects
    (Decimal, datetime, date) into primitive Python types.
    """
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [sanitize_for_json(i) for i in obj]
    return obj


# ---------------------------------------------------------
# Request / Response Models
# ---------------------------------------------------------
class QueryRequest(BaseModel):
    question: str = Field(..., description="The user's natural language question.")
    thread_id: str = Field(
        default="default_user", description="Unique session ID for memory."
    )


class QueryResponse(BaseModel):
    question: str
    intent: str
    answer: str
    result: Optional[Any] = None  # Added for UI client backward compatibility
    tool_result: Optional[Any] = None  # Standard V2 API key
    execution_time: float


# ---------------------------------------------------------
# Endpoints
# ---------------------------------------------------------
@app.get("/health")
async def health():
    return {"status": "healthy", "service": "delhivery-agentic-ai", "version": "2.0.0"}


@app.post("/ask", response_model=QueryResponse)
async def ask(request: QueryRequest):
    start_time = time.time()

    try:
        # ⭐ NEW: Pass the thread_id to the agent for conversational memory
        raw_result = await asyncio.to_thread(
            agent.ask, request.question, thread_id=request.thread_id
        )
        sanitized = sanitize_for_json(raw_result)

        intent = sanitized.get("intent", "UNKNOWN")

        raw_answer = sanitized.get("answer")
        if isinstance(raw_answer, dict):
            answer = (
                raw_answer.get("answer") or raw_answer.get("result") or str(raw_answer)
            )
        elif isinstance(raw_answer, str) and raw_answer.strip():
            answer = raw_answer
        else:
            answer = "No response generated."

        tool_res = sanitized.get("tool_result")
        if not isinstance(tool_res, dict):
            tool_res = {"data": tool_res} if tool_res is not None else {}

        return QueryResponse(
            question=request.question,
            intent=intent,
            answer=answer,
            result=tool_res,
            tool_result=tool_res,
            execution_time=round(time.time() - start_time, 3),
        )

    except Exception as exc:
        import traceback
        traceback.print_exc()  # This forces the full error to print in the terminal
        raise HTTPException(status_code=500, detail=str(exc))


# ⭐ NEW: Upload Endpoint for Dynamic RAG
@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    try:
        file_path = os.path.join(UPLOAD_DIR, file.filename)

        # 1. Save the file locally
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 2. Only process PDFs through FAISS
        if file.filename.lower().endswith(".pdf"):
            result = ingest_pdf_to_faiss(file_path)
            return {
                "status": "success",
                "message": f"Successfully vectorized {file.filename}",
                "faiss_details": result,
            }

        return {
            "status": "success",
            "message": f"Saved {file.filename} (No vectorization applied).",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
