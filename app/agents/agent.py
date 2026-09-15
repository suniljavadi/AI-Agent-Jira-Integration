import re
import time
from dataclasses import dataclass, field
from uuid import uuid4

from pydantic import ValidationError

from app.jira.schemas import CreateIssueRequest, SearchRequest, UpdateIssueRequest
from app.rag.knowledge import KnowledgeBase
from app.tools.jira_tools import JiraTools


INTENTS = ("CREATE_ISSUE", "SEARCH_ISSUES", "GET_ISSUE", "UPDATE_ISSUE", "COMMENT", "ASSIGN", "TRANSITION", "SUMMARIZE", "GENERAL_QUERY")
MUTATING = {"CREATE_ISSUE", "UPDATE_ISSUE", "COMMENT", "ASSIGN", "TRANSITION"}


@dataclass
class PendingAction:
    approval_id: str
    intent: str
    arguments: dict
    summary: str
    expires_at: float


@dataclass
class Conversation:
    pending: PendingAction | None = None
    context: dict = field(default_factory=dict)


class EngineeringAgent:
    def __init__(self, tools: JiraTools, knowledge: KnowledgeBase | None = None):
        self.tools = tools
        self.knowledge = knowledge or KnowledgeBase()
        self.conversations: dict[str, Conversation] = {}

    def classify_intent(self, text: str) -> str:
        lower = text.lower()
        if re.search(r"\b(search|find|show|list)\b", lower): return "SEARCH_ISSUES"
        if re.search(r"\b(create|file|raise)\b", lower) or re.search(r"\bopen\b.*\b(bug|task|story|issue)\b", lower): return "CREATE_ISSUE"
        if re.search(r"\b(comment|add.*note|latest investigation)\b", lower): return "COMMENT"
        if re.search(r"\b(assign|owner|backend team|frontend team)\b", lower): return "ASSIGN"
        if re.search(r"\b(close|resolve|start|move|transition)\b", lower): return "TRANSITION"
        if re.search(r"\b(update|change|edit)\b", lower): return "UPDATE_ISSUE"
        if re.search(r"\b[A-Z]{2,10}-\d+\b", text): return "GET_ISSUE"
        if "summar" in lower or "this week" in lower: return "SUMMARIZE"
        return "GENERAL_QUERY"

    def chat(self, text: str, conversation_id: str | None = None, approve: bool = False) -> dict:
        conversation_id = conversation_id or str(uuid4())
        conversation = self.conversations.setdefault(conversation_id, Conversation())
        if conversation.pending and approve:
            pending = conversation.pending
            conversation.pending = None
            return self._execute(pending.intent, pending.arguments, conversation_id)
        if conversation.pending and text.strip().lower() in {"approve", "approved", "yes"}:
            pending = conversation.pending
            conversation.pending = None
            return self._execute(pending.intent, pending.arguments, conversation_id)
        intent = self.classify_intent(text)
        arguments = self._arguments(intent, text, conversation)
        if intent in MUTATING:
            approval_id = str(uuid4())
            summary = f"Approve {intent.replace('_', ' ').lower()} with {arguments}?"
            conversation.pending = PendingAction(approval_id, intent, arguments, summary, time.time() + 1800)
            return {"conversation_id": conversation_id, "intent": intent, "requires_approval": True, "approval_id": approval_id, "message": summary, "evidence": self.knowledge.retrieve(text)}
        try:
            result = self._run(intent, arguments)
            return {"conversation_id": conversation_id, "intent": intent, "requires_approval": False, "message": self._format(intent, result), "data": result}
        except (ValueError, LookupError, ValidationError) as exc:
            return {"conversation_id": conversation_id, "intent": intent, "requires_approval": False, "error": str(exc)}

    def _arguments(self, intent: str, text: str, conversation: Conversation) -> dict:
        key = (re.search(r"\b[A-Z]{2,10}-\d+\b", text) or [None])[0]
        lower = text.lower()
        if intent == "CREATE_ISSUE":
            issue_type = "Bug" if "bug" in lower else "Task"
            priority = next((p for p in ("CRITICAL", "HIGH", "MEDIUM", "LOW") if p.lower() in lower), None)
            summary = re.sub(r"\b(create|open|file|raise|a|an|bug|task|story|for)\b", "", text, flags=re.I).strip(" .") or "Engineering work"
            return CreateIssueRequest(issue_type=issue_type, summary=summary, priority=priority or "MEDIUM").model_dump()
        if intent == "SEARCH_ISSUES":
            priority = next((p for p in ("CRITICAL", "HIGH", "MEDIUM", "LOW") if p.lower() in lower), None)
            return SearchRequest(query="", priority=priority).model_dump()
        if intent in {"GET_ISSUE", "COMMENT", "ASSIGN", "TRANSITION", "UPDATE_ISSUE"}:
            if not key: key = conversation.context.get("issue_key")
            if not key: raise ValueError("Please include an issue key such as ENG-1")
            conversation.context["issue_key"] = key
            if intent == "COMMENT": return {"key": key, "body": text}
            if intent == "ASSIGN": return {"key": key, "assignee": "backend-team" if "backend" in lower else "frontend-team"}
            if intent == "TRANSITION": return {"key": key, "status": "CLOSED" if "close" in lower else "IN_PROGRESS"}
            if intent == "UPDATE_ISSUE": return {"key": key, "arguments": UpdateIssueRequest(description=text).model_dump()}
            return {"key": key}
        return {}

    def _run(self, intent: str, arguments: dict):
        if intent == "GET_ISSUE": return self.tools.get_issue(arguments["key"])
        if intent == "SEARCH_ISSUES" or intent == "SUMMARIZE": return self.tools.search_issues(SearchRequest(**arguments))
        return {"message": "I can help with Jira issues, searches, comments, assignments, and workflow transitions."}

    def _execute(self, intent: str, arguments: dict, conversation_id: str):
        try:
            result = self._run_mutation(intent, arguments)
            return {"conversation_id": conversation_id, "intent": intent, "requires_approval": False, "message": self._format(intent, result), "data": result, "approval_status": "approved"}
        except (ValueError, LookupError, ValidationError) as exc:
            return {"conversation_id": conversation_id, "intent": intent, "error": str(exc), "approval_status": "approved"}

    def _run_mutation(self, intent: str, arguments: dict):
        if intent == "CREATE_ISSUE": return self.tools.create_issue(CreateIssueRequest(**arguments))
        if intent == "COMMENT": return self.tools.add_comment(arguments["key"], arguments["body"])
        if intent == "ASSIGN": return self.tools.assign_issue(arguments["key"], arguments["assignee"])
        if intent == "TRANSITION": return self.tools.transition_issue(arguments["key"], arguments["status"])
        if intent == "UPDATE_ISSUE": return self.tools.update_issue(arguments["key"], UpdateIssueRequest(**arguments["arguments"]))
        raise ValueError("Unsupported action")

    @staticmethod
    def _format(intent: str, result) -> str:
        if isinstance(result, list): return f"Found {len(result)} issue(s)."
        if isinstance(result, dict) and result.get("key"): return f"{intent.replace('_', ' ').title()} completed for {result['key']}."
        return result.get("message", "Completed.") if isinstance(result, dict) else "Completed."
