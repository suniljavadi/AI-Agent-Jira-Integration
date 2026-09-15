import time
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.agents.agent import EngineeringAgent
from app.database.session import get_db, init_db
from app.jira.schemas import AssignRequest, CommentRequest, CreateIssueRequest, SearchRequest, TransitionRequest, UpdateIssueRequest
from app.jira.service import JiraService
from app.models import AuditEvent
from app.security.auth import require_auth
from app.tools.jira_tools import JiraTools

app = FastAPI(title="AI Engineering Assistant", version="1.0.0")
_agent = None


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=10000)
    conversation_id: str | None = None
    approve: bool = False


class ApprovalRequest(BaseModel):
    conversation_id: str
    approval_id: str


def get_agent(db: Session) -> EngineeringAgent:
    global _agent
    service = JiraService(db)
    service.seed()
    if _agent is None:
        _agent = EngineeringAgent(JiraTools(service))
    else:
        _agent.tools = JiraTools(service)
    return _agent


@app.on_event("startup")
def startup() -> None: init_db()


@app.get("/health")
def health(): return {"status": "ok", "mode": "mock"}


@app.post("/api/v1/chat")
def chat(request: ChatRequest, db: Session = Depends(get_db), actor: str = Depends(require_auth)):
    started = time.perf_counter()
    agent = get_agent(db)
    result = agent.chat(request.message, request.conversation_id, request.approve)
    db.add(AuditEvent(request_id=str(uuid4()), actor=actor, action=result.get("intent", "chat"), payload={"message": request.message, "result": result}, approval_status=result.get("approval_status", "pending" if result.get("requires_approval") else "not_required")))
    db.commit()
    result["latency_ms"] = round((time.perf_counter() - started) * 1000, 2)
    return result


@app.post("/api/v1/approve")
def approve(request: ApprovalRequest, db: Session = Depends(get_db), actor: str = Depends(require_auth)):
    agent = get_agent(db)
    pending = agent.conversations.get(request.conversation_id)
    if not pending or not pending.pending or pending.pending.approval_id != request.approval_id:
        raise HTTPException(400, "Approval is missing, expired, or does not match the pending action")
    return agent.chat("Approve", request.conversation_id, approve=True)


@app.post("/api/v1/issues")
def create_issue(request: CreateIssueRequest, db: Session = Depends(get_db), actor: str = Depends(require_auth)):
    service = JiraService(db); service.seed()
    try: return service.create_issue(request, actor)
    except (ValueError, LookupError) as exc: raise HTTPException(400, str(exc)) from exc


@app.get("/api/v1/issues/{key}")
def get_issue(key: str, db: Session = Depends(get_db), actor: str = Depends(require_auth)):
    service = JiraService(db); service.seed()
    try: return service.get_issue(key)
    except LookupError as exc: raise HTTPException(404, str(exc)) from exc


@app.get("/api/v1/search")
def search(query: str = Query(default=""), priority: str | None = None, status: str | None = None, db: Session = Depends(get_db), actor: str = Depends(require_auth)):
    service = JiraService(db); service.seed()
    return service.search_issues(SearchRequest(query=query, priority=priority, status=status))


@app.patch("/api/v1/issues/{key}")
def update_issue(key: str, request: UpdateIssueRequest, db: Session = Depends(get_db), actor: str = Depends(require_auth)):
    service = JiraService(db); service.seed()
    try: return service.update_issue(key, request)
    except LookupError as exc: raise HTTPException(404, str(exc)) from exc


@app.post("/api/v1/issues/{key}/comments")
def comment(key: str, request: CommentRequest, db: Session = Depends(get_db), actor: str = Depends(require_auth)):
    service = JiraService(db); service.seed()
    try: return service.add_comment(key, request.body, actor)
    except LookupError as exc: raise HTTPException(404, str(exc)) from exc


@app.post("/api/v1/issues/{key}/assign")
def assign(key: str, request: AssignRequest, db: Session = Depends(get_db), actor: str = Depends(require_auth)):
    service = JiraService(db); service.seed()
    try: return service.assign_issue(key, request.assignee)
    except (ValueError, LookupError) as exc: raise HTTPException(400, str(exc)) from exc


@app.post("/api/v1/issues/{key}/transition")
def transition(key: str, request: TransitionRequest, db: Session = Depends(get_db), actor: str = Depends(require_auth)):
    service = JiraService(db); service.seed()
    try: return service.transition_issue(key, request.status)
    except (ValueError, LookupError) as exc: raise HTTPException(400, str(exc)) from exc
