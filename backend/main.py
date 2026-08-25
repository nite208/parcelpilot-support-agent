import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

from auth import login, get_current_user, require_internal
from agent.graph import run_agent
from agent.tools.escalation import confirm_escalation, get_all_escalations
from rag.ingest import ingest_documents
from db.setup import setup_database

app = FastAPI(title="ParcelPilot Support Agent", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class LoginRequest(BaseModel):
    username: str
    password: str


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: List[ChatMessage] = []


class ConfirmEscalationRequest(BaseModel):
    ref_id: str
    ref_type: str
    reason: str


@app.on_event("startup")
def startup():
    setup_database()
    ingest_documents()


@app.get("/")
def root():
    return {"status": "ParcelPilot Support Agent is running"}


@app.post("/auth/login")
def auth_login(request: LoginRequest):
    return login(request.username, request.password)


@app.post("/chat/customer")
def customer_chat(request: ChatRequest, user=Depends(get_current_user)):
    if user.get("role") != "customer":
        raise HTTPException(status_code=403, detail="Customer access only")
    
    account_id = user.get("account_id")
    if not account_id:
        raise HTTPException(status_code=400, detail="No account associated with this user")

    history = [{"role": m.role, "content": m.content} for m in request.history]

    result = run_agent(
        message=request.message,
        history=history,
        account_id=account_id,
        role="customer"
    )

    return {
        "response": result["response"],
        "tool_trace": result["tool_trace"],
        "account_id": account_id
    }


@app.post("/chat/internal")
def internal_chat(request: ChatRequest, user=Depends(require_internal)):
    history = [{"role": m.role, "content": m.content} for m in request.history]

    result = run_agent(
        message=request.message,
        history=history,
        account_id=None,
        role="internal"
    )

    return {
        "response": result["response"],
        "tool_trace": result["tool_trace"],
        "role": "internal"
    }


@app.post("/escalation/confirm")
def confirm_escalation_endpoint(
    request: ConfirmEscalationRequest,
    user=Depends(get_current_user)
):
    account_id = user.get("account_id")
    role = user.get("role")

    escalation = confirm_escalation(
        ref_id=request.ref_id,
        ref_type=request.ref_type,
        reason=request.reason,
        account_id=account_id,
        role=role
    )

    return {
        "message": "Escalation created successfully",
        "escalation": escalation
    }


@app.get("/escalations")
def list_escalations(user=Depends(require_internal)):
    return {"escalations": get_all_escalations()}


@app.get("/health")
def health():
    return {"status": "ok"}